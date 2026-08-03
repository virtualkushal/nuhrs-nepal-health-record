"""
API views for SwasthyaEHR (v2 — multi-department OPD).

Covers: health, email login + change-password, staff self-register + admin
approval, patient registration + directory + portal, encounters + status queue,
nurse vitals, lab catalog/orders/reports/results, prescriptions (pharmacy queue),
ICD-10 diagnoses, the read-only FHIR R4 layer, and cross-hospital sharing
(request -> patient approval -> FHIR Bundle).

Backend RBAC is enforced by EnforceStrictRole via each view's allowed_roles.
There is NO blocking drug-allergy interceptor in v2 (allergies are shown to the
doctor as a red banner instead).
"""

import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .constants import (
    AccessRequestStatus,
    DiagnosisStatus,
    Department,
    EncounterStatus,
    ICD10,
    LabCategory,
    LabOrderStatus,
    LabTestCatalog,
    PrescriptionStatus,
    RegisteredBy,
    Role,
    StaffStatus,
)
from .fhir_serializers import (
    build_everything_bundle,
    condition_to_fhir,
    encounter_to_fhir,
    medicationrequest_to_fhir,
    observation_to_fhir,
    patient_to_fhir,
)
from .models import (
    AccessRequest,
    Diagnosis,
    Encounter,
    LabOrder,
    LabReport,
    LabResult,
    Patient,
    Prescription,
    Vitals,
)
from .permissions import EnforceStrictRole
from .serializers import (
    AccessRequestSerializer,
    ChangePasswordSerializer,
    DiagnosisSerializer,
    EncounterSerializer,
    LabOrderSerializer,
    LabReportSerializer,
    LabResultSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PatientSerializer,
    PrescriptionSerializer,
    StaffCreateSerializer,
    StaffRegisterSerializer,
    StaffSerializer,
    VitalsSerializer,
)

FHIR_CONTENT_TYPE = "application/fhir+json"
FHIR_READ_ROLES = [Role.ADMIN, Role.DOCTOR, Role.PHARMACIST, Role.LAB_TECH, Role.NURSE]

Staff = get_user_model()
FRONTEND_URL = "http://localhost:3000"


def _fhir_error(msg, code="not-found", http=status.HTTP_404_NOT_FOUND):
    return Response(
        {
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "error", "code": code, "diagnostics": msg}],
        },
        status=http,
        content_type=FHIR_CONTENT_TYPE,
    )


def _generate_password():
    return secrets.token_urlsafe(9)


def _email_credentials(user, password):
    """Send login credentials (console backend in dev)."""
    send_mail(
        subject="Your SwasthyaEHR account is ready",
        message=(
            f"Hello {user.full_name},\n\n"
            f"Your account has been approved.\n"
            f"Login email: {user.email}\n"
            f"Temporary password: {password}\n\n"
            f"Please sign in at {FRONTEND_URL}/login and change your password.\n"
        ),
        from_email="noreply@swasthya.org.np",
        recipient_list=[user.email],
        fail_silently=True,
    )


# --------------------------------------------------------------------------- #
# Health & auth
# --------------------------------------------------------------------------- #


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "service": "swasthya-ehr-api"})


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response(
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "department": u.department,
                "status": u.status,
                "must_change_password": u.must_change_password,
                "is_active": u.is_active,
            }
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password", "updated_at"])
        return Response({"detail": "Password changed successfully."})


class StaffRegisterView(generics.CreateAPIView):
    """Public staff self-registration -> PENDING (cannot log in until approved)."""

    permission_classes = [AllowAny]
    serializer_class = StaffRegisterSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            "detail": "Registration received. An administrator will review and "
            "approve your account shortly.",
            "id": response.data.get("id"),
        }
        return response


# --------------------------------------------------------------------------- #
# Staff management + approval (ADMIN)
# --------------------------------------------------------------------------- #


class StaffListCreateView(generics.ListCreateAPIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.ADMIN]

    def get_queryset(self):
        qs = Staff.objects.all().order_by("-created_at")
        status_param = self.request.query_params.get("status")
        role_param = self.request.query_params.get("role")
        if status_param:
            qs = qs.filter(status=status_param)
        if role_param:
            qs = qs.filter(role=role_param)
        return qs

    def get_serializer_class(self):
        return StaffCreateSerializer if self.request.method == "POST" else StaffSerializer


class StaffDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.ADMIN]
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

    def perform_update(self, serializer):
        target = self.get_object()
        if (
            target.id == self.request.user.id
            and self.request.data.get("is_active") is False
        ):
            from rest_framework.exceptions import ValidationError

            raise ValidationError("You cannot deactivate your own account.")
        serializer.save()


class StaffApproveView(APIView):
    """ADMIN approves a PENDING staff account: generate + email a password."""

    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.ADMIN]

    def post(self, request, pk):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response({"detail": "Staff not found."}, status=404)
        if staff.status == StaffStatus.ACTIVE:
            return Response({"detail": "Already active."}, status=400)

        password = _generate_password()
        staff.status = StaffStatus.ACTIVE
        staff.is_active = True
        staff.must_change_password = True
        staff.set_password(password)
        staff.save()
        _email_credentials(staff, password)
        return Response(
            {"detail": f"{staff.full_name} approved. Credentials emailed."}
        )


class StaffRejectView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.ADMIN]

    def post(self, request, pk):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response({"detail": "Staff not found."}, status=404)
        staff.status = StaffStatus.REJECTED
        staff.is_active = False
        staff.save(update_fields=["status", "is_active", "updated_at"])
        return Response({"detail": f"{staff.full_name} rejected."})


class AdminOverviewView(APIView):
    """ADMIN dashboard summary counts."""

    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.ADMIN]

    def get(self, request):
        return Response(
            {
                "patients": Patient.objects.count(),
                "encounters_open": Encounter.objects.exclude(
                    status=EncounterStatus.CLOSED
                ).count(),
                "staff_active": Staff.objects.filter(
                    status=StaffStatus.ACTIVE
                ).count(),
                "staff_pending": Staff.objects.filter(
                    status=StaffStatus.PENDING
                ).count(),
                "by_role": {
                    role: Staff.objects.filter(role=role).count()
                    for role, _ in Role.CHOICES
                },
            }
        )


# --------------------------------------------------------------------------- #
# Reference catalogs (departments, lab tests, ICD-10)
# --------------------------------------------------------------------------- #


@api_view(["GET"])
@permission_classes([AllowAny])
def departments_catalog(request):
    return Response(
        {"results": [{"code": c, "name": n} for c, n in Department.CHOICES]}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def lab_catalog(request):
    """The orderable lab test catalog, optionally filtered by ?department=."""
    dept = request.query_params.get("department")
    tests = LabTestCatalog.for_department(dept) if dept else LabTestCatalog.TESTS
    results = [
        {
            "code": code,
            "name": meta["name"],
            "category": meta["category"],
            "type": meta["type"],
            "loinc": meta.get("loinc", ""),
            "unit": meta.get("unit", ""),
            "reference_low": meta.get("low"),
            "reference_high": meta.get("high"),
        }
        for code, meta in tests.items()
    ]
    return Response({"count": len(results), "results": results})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def icd10_catalog(request):
    """ICD-10 vocabulary, optionally filtered by ?department=."""
    dept = request.query_params.get("department")
    entries = ICD10.for_department(dept) if dept else ICD10.ENTRIES
    results = [
        {"code": code, "name": meta["name"], "department": meta["dept"]}
        for code, meta in entries.items()
    ]
    return Response({"count": len(results), "results": results})


# --------------------------------------------------------------------------- #
# Patient registration & directory
# --------------------------------------------------------------------------- #


class PatientSelfRegisterView(generics.CreateAPIView):
    """Public self-registration. Creates a linked PATIENT login + emails password."""

    permission_classes = [AllowAny]
    serializer_class = PatientSerializer

    def perform_create(self, serializer):
        email = (serializer.validated_data.pop("email", "") or "").strip().lower()
        with transaction.atomic():
            user = None
            password = None
            if email:
                password = _generate_password()
                user = Staff(
                    email=email,
                    full_name=(
                        f"{serializer.validated_data.get('first_name', '')} "
                        f"{serializer.validated_data.get('last_name', '')}"
                    ).strip(),
                    role=Role.PATIENT,
                    status=StaffStatus.ACTIVE,
                    is_active=True,
                    must_change_password=True,
                )
                user.set_password(password)
                user.save()
            patient = serializer.save(registered_by=RegisteredBy.SELF, user=user)
            if user and password:
                _email_credentials(user, password)
            self._created_patient = patient


class PatientListCreateView(generics.ListCreateAPIView):
    """Directory (read: clinical roles) + receptionist intake (write)."""

    serializer_class = PatientSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR, Role.PHARMACIST, Role.RECEPTIONIST, Role.NURSE]

    def get_queryset(self):
        qs = Patient.objects.all().order_by("-created_at")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(hospital_identifier__icontains=search)
                | Q(national_id__icontains=search)
                | Q(phone_number__icontains=search)
            )
        return qs

    def create(self, request, *args, **kwargs):
        if request.user.role != Role.RECEPTIONIST:
            return Response(
                {"detail": "Only a receptionist can register patients here."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        email = (serializer.validated_data.pop("email", "") or "").strip().lower()
        with transaction.atomic():
            user = None
            password = None
            if email:
                password = _generate_password()
                user = Staff(
                    email=email,
                    full_name=(
                        f"{serializer.validated_data.get('first_name', '')} "
                        f"{serializer.validated_data.get('last_name', '')}"
                    ).strip(),
                    role=Role.PATIENT,
                    status=StaffStatus.ACTIVE,
                    is_active=True,
                    must_change_password=True,
                )
                user.set_password(password)
                user.save()
            serializer.save(registered_by=RegisteredBy.RECEPTIONIST, user=user)
            if user and password:
                _email_credentials(user, password)


class PatientDetailView(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR, Role.PHARMACIST, Role.RECEPTIONIST, Role.NURSE]


def _build_timeline(patient):
    """Shared payload: profile, diagnoses, prescriptions, lab results + trends."""
    results = LabResult.objects.filter(patient=patient).order_by("created_at")
    prescriptions = Prescription.objects.filter(patient=patient).order_by("-created_at")
    diagnoses = Diagnosis.objects.filter(patient=patient).order_by("-created_at")
    encounters = Encounter.objects.filter(patient=patient).order_by("-created_at")

    trends = {}
    for r in results:
        if r.result_value is None:
            continue
        trends.setdefault(
            r.test_code,
            {"test_code": r.test_code, "test_name": r.test_name, "unit": r.result_unit, "points": []},
        )
        trends[r.test_code]["points"].append(
            {"date": r.created_at.isoformat(), "value": float(r.result_value), "flag": r.flag}
        )

    return {
        "patient": PatientSerializer(patient).data,
        "encounters": EncounterSerializer(encounters, many=True).data,
        "prescriptions": PrescriptionSerializer(prescriptions, many=True).data,
        "lab_results": LabResultSerializer(results, many=True).data,
        "diagnoses": DiagnosisSerializer(diagnoses, many=True).data,
        "trends": list(trends.values()),
    }


class PatientTimelineView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR, Role.NURSE]

    def get(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            return Response({"detail": "Patient not found."}, status=404)
        return Response(_build_timeline(patient))


class PatientPortalView(APIView):
    """PATIENT reads only their own linked record."""

    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.PATIENT]

    def get(self, request):
        patient = Patient.objects.filter(user=request.user).first()
        if patient is None:
            return Response(
                {"detail": "No patient profile is linked to this account."},
                status=404,
            )
        return Response(_build_timeline(patient))


# --------------------------------------------------------------------------- #
# Encounters + status queue
# --------------------------------------------------------------------------- #


class EncounterListCreateView(generics.ListCreateAPIView):
    serializer_class = EncounterSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.RECEPTIONIST, Role.NURSE, Role.DOCTOR, Role.LAB_TECH, Role.PHARMACIST]

    def get_queryset(self):
        qs = Encounter.objects.select_related(
            "patient", "attending_doctor"
        ).order_by("-created_at")
        status_param = self.request.query_params.get("status")
        dept_param = self.request.query_params.get("department")
        patient_param = self.request.query_params.get("patient")
        if status_param:
            qs = qs.filter(status=status_param)
        if dept_param:
            qs = qs.filter(department=dept_param)
        if patient_param:
            qs = qs.filter(patient_id=patient_param)
        # Nurses default to encounters awaiting vitals.
        if self.request.user.role == Role.NURSE and not status_param:
            qs = qs.filter(status=EncounterStatus.REGISTERED)
        # Doctors default to their own department + waiting-for-doctor states.
        if self.request.user.role == Role.DOCTOR and not status_param:
            qs = qs.filter(
                department=self.request.user.department,
                status__in=[EncounterStatus.VITALS_DONE, EncounterStatus.WITH_DOCTOR, EncounterStatus.LAB_DONE],
            )
        return qs

    def create(self, request, *args, **kwargs):
        if request.user.role != Role.RECEPTIONIST:
            return Response(
                {"detail": "Only a receptionist can check patients in."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, status=EncounterStatus.REGISTERED)


class EncounterDetailView(generics.RetrieveUpdateAPIView):
    queryset = Encounter.objects.all()
    serializer_class = EncounterSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.RECEPTIONIST, Role.NURSE, Role.DOCTOR]


class EncounterStatusView(APIView):
    """Advance an encounter's status (role-guarded transitions)."""

    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.NURSE, Role.DOCTOR, Role.LAB_TECH]

    def post(self, request, pk):
        try:
            enc = Encounter.objects.get(pk=pk)
        except Encounter.DoesNotExist:
            return Response({"detail": "Encounter not found."}, status=404)
        new_status = request.data.get("status")
        valid = {s for s, _ in EncounterStatus.CHOICES}
        if new_status not in valid:
            return Response({"detail": "Invalid status."}, status=400)
        enc.status = new_status
        enc.save(update_fields=["status", "updated_at"])
        return Response(EncounterSerializer(enc).data)


# --------------------------------------------------------------------------- #
# Vitals (nurse)
# --------------------------------------------------------------------------- #


class VitalsCreateView(generics.CreateAPIView):
    serializer_class = VitalsSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.NURSE]

    def perform_create(self, serializer):
        with transaction.atomic():
            vitals = serializer.save(recorded_by=self.request.user)
            enc = vitals.encounter
            if enc.status == EncounterStatus.REGISTERED:
                enc.status = EncounterStatus.VITALS_DONE
                enc.save(update_fields=["status", "updated_at"])


class VitalsDetailView(generics.RetrieveAPIView):
    queryset = Vitals.objects.all()
    serializer_class = VitalsSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.NURSE, Role.DOCTOR]
    lookup_field = "encounter_id"
    lookup_url_kwarg = "encounter_id"


# --------------------------------------------------------------------------- #
# Lab: orders (doctor) + reports/results (lab tech)
# --------------------------------------------------------------------------- #


class LabOrderListCreateView(generics.ListCreateAPIView):
    serializer_class = LabOrderSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR, Role.LAB_TECH]

    def get_queryset(self):
        qs = LabOrder.objects.select_related("patient", "ordered_by").order_by(
            "-created_at"
        )
        status_param = self.request.query_params.get("status")
        patient_param = self.request.query_params.get("patient")
        if status_param:
            qs = qs.filter(status=status_param)
        elif self.request.user.role == Role.LAB_TECH:
            qs = qs.filter(status=LabOrderStatus.PENDING)
        if patient_param:
            qs = qs.filter(patient_id=patient_param)
        return qs

    def create(self, request, *args, **kwargs):
        if request.user.role != Role.DOCTOR:
            return Response(
                {"detail": "Only a doctor can order a lab test."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(ordered_by=self.request.user)
            enc = order.encounter
            if enc.status in (EncounterStatus.WITH_DOCTOR, EncounterStatus.VITALS_DONE):
                enc.status = EncounterStatus.LAB_PENDING
                enc.save(update_fields=["status", "updated_at"])


class LabReportCreateView(generics.CreateAPIView):
    """LAB_TECH submits a report (order + nested results). Closes the order."""

    serializer_class = LabReportSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.LAB_TECH]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        results_data = serializer.validated_data.pop("results", [])
        lab_order = serializer.validated_data["lab_order"]

        with transaction.atomic():
            report = LabReport.objects.create(
                lab_order=lab_order,
                patient=lab_order.patient,
                entered_by=request.user,
                pdf_file=serializer.validated_data.get("pdf_file"),
                source=serializer.validated_data.get("source", "MANUAL"),
                status=LabReport.CONFIRMED,
            )
            for r in results_data:
                LabResult.objects.create(
                    lab_report=report,
                    patient=lab_order.patient,
                    test_code=r["test_code"],
                    result_value=r.get("result_value"),
                    report_text=r.get("report_text", ""),
                )
            lab_order.status = LabOrderStatus.COMPLETED
            lab_order.save(update_fields=["status", "updated_at"])
            enc = lab_order.encounter
            if not enc.lab_orders.filter(status=LabOrderStatus.PENDING).exists():
                enc.status = EncounterStatus.LAB_DONE
                enc.save(update_fields=["status", "updated_at"])

        return Response(
            LabReportSerializer(report).data, status=status.HTTP_201_CREATED
        )


class LabResultListView(generics.ListAPIView):
    serializer_class = LabResultSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR, Role.LAB_TECH, Role.NURSE]

    def get_queryset(self):
        qs = LabResult.objects.select_related("patient").order_by("-created_at")
        patient_param = self.request.query_params.get("patient")
        if patient_param:
            qs = qs.filter(patient_id=patient_param)
        return qs


# --------------------------------------------------------------------------- #
# Prescriptions (doctor writes, pharmacist dispenses)
# --------------------------------------------------------------------------- #


class PrescriptionCreateView(generics.CreateAPIView):
    """DOCTOR writes a prescription. No blocking allergy check (banner only)."""

    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR]
    serializer_class = PrescriptionSerializer

    def perform_create(self, serializer):
        serializer.save(
            prescribed_by=self.request.user, status=PrescriptionStatus.ACTIVE
        )


class PrescriptionQueueView(generics.ListAPIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.PHARMACIST]
    serializer_class = PrescriptionSerializer

    def get_queryset(self):
        return (
            Prescription.objects.filter(status=PrescriptionStatus.ACTIVE)
            .select_related("patient", "prescribed_by")
            .order_by("-created_at")
        )


class PrescriptionFulfillView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.PHARMACIST]

    def post(self, request, pk):
        try:
            rx = Prescription.objects.get(pk=pk)
        except Prescription.DoesNotExist:
            return Response({"detail": "Prescription not found."}, status=404)
        if rx.status == PrescriptionStatus.COMPLETED:
            return Response({"detail": "Already fulfilled."}, status=400)
        rx.status = PrescriptionStatus.COMPLETED
        rx.fulfilled_by = request.user
        rx.fulfilled_at = timezone.now()
        rx.save()
        return Response(PrescriptionSerializer(rx).data)


# --------------------------------------------------------------------------- #
# Diagnoses (ICD-10 problem list)
# --------------------------------------------------------------------------- #


class DiagnosisListCreateView(generics.ListCreateAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR, Role.PATIENT]

    def get_queryset(self):
        qs = Diagnosis.objects.select_related("patient", "diagnosed_by").order_by(
            "-created_at"
        )
        if self.request.user.role == Role.PATIENT:
            return qs.filter(patient__user=self.request.user)
        patient_param = self.request.query_params.get("patient")
        if patient_param:
            qs = qs.filter(patient_id=patient_param)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(clinical_status=status_param)
        return qs

    def create(self, request, *args, **kwargs):
        if request.user.role != Role.DOCTOR:
            return Response(
                {"detail": "Only a doctor can record a diagnosis."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(diagnosed_by=self.request.user)


class DiagnosisResolveView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR]

    def post(self, request, pk):
        try:
            dx = Diagnosis.objects.get(pk=pk)
        except Diagnosis.DoesNotExist:
            return Response({"detail": "Diagnosis not found."}, status=404)
        if dx.clinical_status == DiagnosisStatus.RESOLVED:
            return Response({"detail": "Already resolved."}, status=400)
        dx.clinical_status = DiagnosisStatus.RESOLVED
        dx.resolved_at = timezone.now()
        dx.save(update_fields=["clinical_status", "resolved_at", "updated_at"])
        return Response(DiagnosisSerializer(dx).data)


# --------------------------------------------------------------------------- #
# FHIR R4 (read-only)
# --------------------------------------------------------------------------- #


class FHIRPatientView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = FHIR_READ_ROLES

    def get(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            return _fhir_error("Patient not found")
        return Response(patient_to_fhir(patient), content_type=FHIR_CONTENT_TYPE)


class FHIRObservationView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = FHIR_READ_ROLES

    def get(self, request, pk):
        try:
            result = LabResult.objects.get(pk=pk)
        except LabResult.DoesNotExist:
            return _fhir_error("Observation not found")
        return Response(observation_to_fhir(result), content_type=FHIR_CONTENT_TYPE)


class FHIRConditionView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = FHIR_READ_ROLES

    def get(self, request, pk):
        try:
            dx = Diagnosis.objects.get(pk=pk)
        except Diagnosis.DoesNotExist:
            return _fhir_error("Condition not found")
        return Response(condition_to_fhir(dx), content_type=FHIR_CONTENT_TYPE)


def _everything(patient, base_url):
    encounters = Encounter.objects.filter(patient=patient).order_by("created_at")
    results = LabResult.objects.filter(patient=patient).order_by("created_at")
    diagnoses = Diagnosis.objects.filter(patient=patient).order_by("created_at")
    prescriptions = Prescription.objects.filter(patient=patient).order_by("created_at")
    return build_everything_bundle(
        patient, encounters, results, diagnoses, prescriptions, base_url
    )


class FHIRPatientEverythingView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = FHIR_READ_ROLES

    def get(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk)
        except Patient.DoesNotExist:
            return _fhir_error("Patient not found")
        bundle = _everything(patient, request.build_absolute_uri("/"))
        return Response(bundle, content_type=FHIR_CONTENT_TYPE)


# --------------------------------------------------------------------------- #
# Cross-hospital sharing: request -> patient approval -> FHIR Bundle
# --------------------------------------------------------------------------- #


class ShareRequestCreateView(APIView):
    """
    External hospital requests a patient's record by National ID. Public
    endpoint (the external system is not a user of this hospital). Returns a
    request id to poll. The patient must approve in their portal.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        national_id = (request.data.get("national_id") or "").strip()
        label = (request.data.get("requester_label") or "").strip()
        requester_hospital = (request.data.get("requester_hospital") or "").strip()
        scope = request.data.get("scope") or []
        if not national_id:
            return Response({"detail": "national_id is required."}, status=400)
        patient = Patient.objects.filter(national_id=national_id).first()
        req = AccessRequest.objects.create(
            patient=patient,
            national_id=national_id,
            requester_label=label,
            requester_hospital=requester_hospital,
            scope=scope,
            status=AccessRequestStatus.PENDING,
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        return Response(
            {
                "request_id": str(req.id),
                "status": req.status,
                "message": "Awaiting patient approval. Poll the status endpoint.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ShareRequestStatusView(APIView):
    """External hospital polls here; on APPROVED it receives the FHIR Bundle."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            req = AccessRequest.objects.get(pk=pk)
        except AccessRequest.DoesNotExist:
            return _fhir_error("Request not found")

        if (
            req.status == AccessRequestStatus.PENDING
            and req.expires_at < timezone.now()
        ):
            req.status = AccessRequestStatus.EXPIRED
            req.save(update_fields=["status", "updated_at"])

        if req.status == AccessRequestStatus.APPROVED and req.patient:
            from .interop_views import scoped_bundle
            bundle = scoped_bundle(
                req.patient, request.build_absolute_uri("/"), req.scope
            )
            return Response(bundle, content_type=FHIR_CONTENT_TYPE)
        if req.status == AccessRequestStatus.PENDING:
            return Response({"status": "PENDING"}, status=status.HTTP_202_ACCEPTED)
        return Response({"status": req.status}, status=status.HTTP_403_FORBIDDEN)


class PatientShareRequestsView(APIView):
    """PATIENT sees pending share requests for their own NID."""

    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.PATIENT]

    def get(self, request):
        patient = Patient.objects.filter(user=request.user).first()
        if not patient:
            return Response({"results": []})
        reqs = AccessRequest.objects.filter(
            Q(patient=patient) | Q(national_id=patient.national_id)
        ).order_by("-created_at")
        return Response({"results": AccessRequestSerializer(reqs, many=True).data})


class PatientShareDecisionView(APIView):
    """PATIENT approves or denies a share request."""

    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.PATIENT]

    def post(self, request, pk):
        patient = Patient.objects.filter(user=request.user).first()
        if not patient:
            return Response({"detail": "No patient profile."}, status=404)
        try:
            req = AccessRequest.objects.get(pk=pk)
        except AccessRequest.DoesNotExist:
            return Response({"detail": "Request not found."}, status=404)
        if req.national_id != patient.national_id:
            return Response({"detail": "Not your request."}, status=403)

        decision = (request.data.get("decision") or "").upper()
        if decision == "APPROVE":
            req.patient = patient
            req.status = AccessRequestStatus.APPROVED
            req.approved_at = timezone.now()
            req.expires_at = timezone.now() + timedelta(minutes=30)
        elif decision == "DENY":
            req.status = AccessRequestStatus.DENIED
        else:
            return Response({"detail": "decision must be APPROVE or DENY."}, status=400)
        req.save()
        return Response(AccessRequestSerializer(req).data)


# --------------------------------------------------------------------------- #
# Password reset
# --------------------------------------------------------------------------- #


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = Staff.objects.filter(email=email, is_active=True).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{FRONTEND_URL}/reset-password/{uid}/{token}/"
            send_mail(
                subject="Reset Your SwasthyaEHR Password",
                message=f"Click the link to reset your password:\n\n{reset_link}",
                from_email="noreply@swasthya.org.np",
                recipient_list=[email],
                fail_silently=True,
            )
        return Response(
            {"detail": "If an account exists with this email, a reset link was sent."}
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        return Response({"detail": "Password has been reset successfully."})
