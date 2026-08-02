"""National Platform API views."""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from . import services
from .models import AuditLog, Organization, PatientIdentity, RecordIndex, User
from .validators import is_valid_nid, normalize_nid

from .serializers import (
    AuditLogSerializer,
    OrganizationRegisterSerializer,
    OrganizationSerializer,
    PatientIdentitySerializer,
    RecordIndexSerializer,
    StaffSerializer,
    UserProfileSerializer,
)


def client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0] if xff else request.META.get("REMOTE_ADDR")


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate

        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        tokens = issue_tokens(user)
        return Response({**tokens, "user": UserProfileSerializer(user).data})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_password = request.data.get("new_password")
        if not new_password or len(new_password) < 6:
            return Response({"detail": "Password too short"}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user.set_password(new_password)
        user.must_change_password = False
        user.save()
        return Response({"detail": "Password updated"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserProfileSerializer(request.user).data)


# ---------------------------------------------------------------------------
# Organization registration & approval
# ---------------------------------------------------------------------------
class OrganizationRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OrganizationRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = serializer.save(status=Organization.Status.PENDING)
        return Response(OrganizationSerializer(org).data, status=status.HTTP_201_CREATED)


class OrganizationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Organization.objects.all().order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(OrganizationSerializer(qs, many=True).data)


class OrganizationApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin can approve"}, status=status.HTTP_403_FORBIDDEN)
        org = Organization.objects.get(pk=pk)
        if org.status == Organization.Status.ACTIVE:
            return Response({"detail": "Already active"}, status=status.HTTP_400_BAD_REQUEST)

        org.organization_code = services.generate_org_code(org.organization_type)
        org.api_key = services.generate_api_key()
        org.status = Organization.Status.ACTIVE
        org.save()

        admin_username = services.generate_admin_username(org.organization_code)
        temp_password = services.generate_temp_password()
        User.objects.create_user(
            username=admin_username,
            password=temp_password,
            full_name=f"{org.organization_name} Admin",
            email=org.contact_email,
            phone=org.contact_phone,
            role=User.Role.ORGANIZATION_ADMIN,
            organization=org,
            must_change_password=True,
        )
        # credentials shown once
        return Response({
            "organization_code": org.organization_code,
            "admin_username": admin_username,
            "temporary_password": temp_password,
            "api_key": org.api_key,
        })


class OrganizationRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != User.Role.SUPER_ADMIN:
            return Response({"detail": "Only super admin can reject"}, status=status.HTTP_403_FORBIDDEN)
        org = Organization.objects.get(pk=pk)
        org.status = Organization.Status.REJECTED
        org.save()
        return Response({"detail": "Rejected"})


# ---------------------------------------------------------------------------
# Organization admin — staff management
# ---------------------------------------------------------------------------
class StaffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        qs = User.objects.filter(organization=org).exclude(role=User.Role.ORGANIZATION_ADMIN)
        return Response(StaffSerializer(qs, many=True).data)

    def post(self, request):
        if request.user.role != User.Role.ORGANIZATION_ADMIN:
            return Response({"detail": "Only org admin"}, status=status.HTTP_403_FORBIDDEN)
        org = request.user.organization
        role = request.data.get("role", User.Role.DOCTOR)
        count = User.objects.filter(organization=org, role=role).count() + 1
        prefix = "DOC" if role == User.Role.DOCTOR else "TECH"
        username = f"{org.organization_code}-{prefix}-{count:04d}"
        temp_password = services.generate_temp_password()
        user = User.objects.create_user(
            username=username,
            password=temp_password,
            full_name=request.data.get("full_name", ""),
            email=request.data.get("email", ""),
            phone=request.data.get("phone", ""),
            role=role,
            organization=org,
            must_change_password=True,
        )
        return Response(
            {**StaffSerializer(user).data, "temporary_password": temp_password},
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Exchange engine (doctor)
# ---------------------------------------------------------------------------
class PatientLookupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, nid):
        try:
            patient = PatientIdentity.objects.get(nid=nid)
        except PatientIdentity.DoesNotExist:
            return Response({"detail": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        AuditLog.objects.create(
            actor_user=request.user, actor_org=request.user.organization,
            nid=nid, action=AuditLog.Action.SEARCH, ip_address=client_ip(request),
        )
        return Response(PatientIdentitySerializer(patient).data)


class PatientIndexView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, nid):
        qs = RecordIndex.objects.filter(patient__nid=nid).select_related("organization")
        return Response(RecordIndexSerializer(qs, many=True).data)


class PatientFetchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nid):
        mode = request.data.get("mode", "ALL")
        engine = services.RoutingEngine(actor_user=request.user, ip_address=client_ip(request))
        if mode == "ONE":
            record_index_id = request.data.get("record_index_id")
            bundle = engine.fetch_one(nid, record_index_id)
        else:
            bundle = engine.fetch_all(nid)
        return Response(bundle)


# ---------------------------------------------------------------------------
# Patient portal
# ---------------------------------------------------------------------------
class PatientActivateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        nid = normalize_nid(request.data.get("nid"))
        dob = request.data.get("date_of_birth")
        phone = request.data.get("phone")
        password = request.data.get("password")
        if not is_valid_nid(nid):
            return Response(
                {"detail": "National ID must be exactly 11 digits (Nepal NIN)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:

            patient = PatientIdentity.objects.get(nid=nid, date_of_birth=dob, phone=phone)
        except PatientIdentity.DoesNotExist:
            return Response({"detail": "Identity verification failed"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=nid).exists():
            return Response({"detail": "Account already activated"}, status=status.HTTP_400_BAD_REQUEST)
        User.objects.create_user(
            username=nid, password=password, full_name=patient.full_name,
            email=patient.email, phone=patient.phone,
            role=User.Role.PATIENT, patient_identity=patient,
        )
        return Response({"detail": "Account activated"}, status=status.HTTP_201_CREATED)


class PatientMyRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.PATIENT or not request.user.patient_identity:
            return Response({"detail": "Not a patient account"}, status=status.HTTP_403_FORBIDDEN)
        nid = request.user.patient_identity.nid
        qs = RecordIndex.objects.filter(patient__nid=nid).select_related("organization")
        return Response({
            "patient": PatientIdentitySerializer(request.user.patient_identity).data,
            "records": RecordIndexSerializer(qs, many=True).data,
        })


# ---------------------------------------------------------------------------
# Metadata ingest (called by hospitals/labs with X-API-Key)
# ---------------------------------------------------------------------------
class IndexIngestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        api_key = request.headers.get("X-API-Key")
        try:
            org = Organization.objects.get(api_key=api_key, status=Organization.Status.ACTIVE)
        except Organization.DoesNotExist:
            return Response({"detail": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        p = request.data.get("patient", {})
        nid = normalize_nid(request.data.get("nid") or p.get("nid"))
        if not is_valid_nid(nid):
            return Response(
                {"detail": "National ID must be exactly 11 digits (Nepal NIN)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        patient, _ = PatientIdentity.objects.get_or_create(
            nid=nid,

            defaults={
                "full_name": p.get("full_name", ""),
                "date_of_birth": p.get("date_of_birth"),
                "gender": p.get("gender", PatientIdentity.Gender.OTHER),
                "phone": p.get("phone", ""),
                "email": p.get("email", ""),
            },
        )
        record = RecordIndex.objects.create(
            patient=patient,
            organization=org,
            resource_type=request.data.get("resource_type"),
            local_record_id=request.data.get("local_record_id"),
            service_date=request.data.get("service_date"),
            summary=request.data.get("summary", ""),
        )
        return Response({"detail": "indexed", "record_index_id": record.id}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Audit & analytics
# ---------------------------------------------------------------------------
class AuditLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AuditLog.objects.all().select_related("actor_user", "actor_org")
        if request.query_params.get("nid"):
            qs = qs.filter(nid=request.query_params["nid"])
        if request.query_params.get("action"):
            qs = qs.filter(action=request.query_params["action"])
        return Response(AuditLogSerializer(qs[:200], many=True).data)


class AnalyticsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Count

        top_conditions = list(
            RecordIndex.objects.filter(resource_type=RecordIndex.ResourceType.CONDITION)
            .values("summary")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        by_province = list(
            RecordIndex.objects.values("organization__province")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response({
            "total_records_indexed": RecordIndex.objects.count(),
            "total_patients": PatientIdentity.objects.count(),
            "total_organizations": Organization.objects.filter(status=Organization.Status.ACTIVE).count(),
            "total_exchanges": AuditLog.objects.filter(
                action__in=[AuditLog.Action.FETCH_ALL, AuditLog.Action.FETCH_ONE]
            ).count(),
            "top_conditions": top_conditions,
            "records_by_province": by_province,
        })
