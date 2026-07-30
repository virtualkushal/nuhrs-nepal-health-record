"""
Serializers for SwasthyaEHR (v2 — multi-department OPD).

Backend is the source of truth for validation (REQ-V1..V3). Login is by email.
Staff self-register (PENDING) and an admin approves them. Patients register a
profile and get a linked login account.
"""

import re
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .constants import (
    BloodGroup,
    Department,
    ICD10,
    LabResultType,
    LabTestCatalog,
    Role,
    StaffStatus,
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

Staff = get_user_model()

# --------------------------------------------------------------------------- #
# Reusable field validators
# --------------------------------------------------------------------------- #

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z\s.'-]{1,49}$")
# Nepali mobile: +977-98XXXXXXXX or 98XXXXXXXX (10 digits starting 97/98).
PHONE_RE = re.compile(r"^(\+977[-\s]?)?9[78]\d{8}$")
NID_RE = re.compile(r"^\d{10,12}$")


def validate_person_name(value):
    value = (value or "").strip()
    if not NAME_RE.match(value):
        raise serializers.ValidationError(
            "Must be 2–50 letters (spaces, hyphen, apostrophe allowed)."
        )
    return value


def validate_phone(value):
    value = (value or "").strip()
    if not PHONE_RE.match(value):
        raise serializers.ValidationError(
            "Enter a valid Nepali mobile number, e.g. +977-9841234567."
        )
    return value


def validate_dob(value):
    if value > date.today():
        raise serializers.ValidationError("Date of birth cannot be in the future.")
    age = (date.today() - value).days // 365
    if age > 120:
        raise serializers.ValidationError("Age cannot exceed 120 years.")
    return value


# --------------------------------------------------------------------------- #
# Staff / auth
# --------------------------------------------------------------------------- #


class StaffSerializer(serializers.ModelSerializer):
    """Read/list representation of a staff account (no password exposed)."""

    class Meta:
        model = Staff
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "department",
            "status",
            "must_change_password",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StaffRegisterSerializer(serializers.ModelSerializer):
    """
    Public staff self-registration. Creates a PENDING account with no usable
    password (set on admin approval). Admin/patient roles cannot self-register.
    """

    class Meta:
        model = Staff
        fields = ["id", "email", "full_name", "role", "department"]
        read_only_fields = ["id"]

    def validate_full_name(self, value):
        return validate_person_name(value)

    def validate_email(self, value):
        value = value.lower().strip()
        if Staff.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email exists.")
        return value

    def validate_role(self, value):
        if value not in Role.STAFF_ROLES:
            raise serializers.ValidationError(
                "You can only self-register as a clinical staff role."
            )
        return value

    def validate(self, attrs):
        if attrs.get("role") == Role.DOCTOR and not attrs.get("department"):
            raise serializers.ValidationError(
                {"department": "A doctor must select a department."}
            )
        return attrs

    def create(self, validated_data):
        staff = Staff(
            **validated_data,
            status=StaffStatus.PENDING,
            is_active=False,  # cannot log in until approved
            must_change_password=True,
        )
        staff.set_unusable_password()
        staff.save()
        return staff


class StaffCreateSerializer(serializers.ModelSerializer):
    """ADMIN-created staff account (immediately ACTIVE)."""

    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = Staff
        fields = ["id", "email", "full_name", "role", "department", "password"]
        read_only_fields = ["id"]

    def validate_role(self, value):
        valid = {c[0] for c in Role.CHOICES}
        if value not in valid:
            raise serializers.ValidationError(f"'{value}' is not a valid role.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        staff = Staff(
            **validated_data,
            status=StaffStatus.ACTIVE,
            is_active=True,
            must_change_password=bool(password is None),
        )
        if password:
            staff.set_password(password)
        else:
            staff.set_unusable_password()
        staff.save()
        return staff


class LoginSerializer(TokenObtainPairSerializer):
    """Email + password login. Embeds role + identity in the token."""

    username_field = "email"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.status == StaffStatus.PENDING:
            raise serializers.ValidationError(
                "Your account is awaiting administrator approval."
            )
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "full_name": self.user.full_name,
            "role": self.user.role,
            "department": self.user.department,
            "must_change_password": self.user.must_change_password,
        }
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Authenticated user sets a new password (clears must_change_password)."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


# --------------------------------------------------------------------------- #
# Patient
# --------------------------------------------------------------------------- #


class PatientSerializer(serializers.ModelSerializer):
    """Create/read a patient profile with full backend validation."""

    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    age = serializers.SerializerMethodField(read_only=True)
    has_login = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "hospital_identifier",
            "national_id",
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "age",
            "gender",
            "blood_group",
            "allergies",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "marital_status",
            "occupation",
            "registered_by",
            "email",
            "has_login",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "hospital_identifier",
            "registered_by",
            "created_at",
        ]

    def get_age(self, obj):
        if obj.date_of_birth:
            return (date.today() - obj.date_of_birth).days // 365
        return None

    def get_has_login(self, obj):
        return obj.user_id is not None

    def validate_first_name(self, value):
        return validate_person_name(value)

    def validate_last_name(self, value):
        return validate_person_name(value)

    def validate_phone_number(self, value):
        return validate_phone(value)

    def validate_date_of_birth(self, value):
        return validate_dob(value)

    def validate_national_id(self, value):
        value = (value or "").strip()
        if not NID_RE.match(value):
            raise serializers.ValidationError(
                "National ID must be 10–12 digits."
            )
        qs = Patient.objects.filter(national_id=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A patient with this National ID already exists."
            )
        return value

    def validate_blood_group(self, value):
        if value not in BloodGroup.VALUES:
            raise serializers.ValidationError("Invalid blood group.")
        return value

    def validate_allergies(self, value):
        """Free-text allergies (v2): a list of non-empty strings."""
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Allergies must be a list of strings.")
        cleaned = []
        for item in value:
            text = str(item).strip()
            if text:
                cleaned.append(text[:100])
        return cleaned

    def validate_email(self, value):
        value = (value or "").lower().strip()
        if value and Staff.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value


# --------------------------------------------------------------------------- #
# Encounter & Vitals
# --------------------------------------------------------------------------- #


class EncounterSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    hospital_identifier = serializers.CharField(
        source="patient.hospital_identifier", read_only=True
    )
    doctor_name = serializers.CharField(
        source="attending_doctor.full_name", read_only=True, default=None
    )
    department_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Encounter
        fields = [
            "id",
            "patient",
            "patient_name",
            "hospital_identifier",
            "department",
            "department_display",
            "attending_doctor",
            "doctor_name",
            "created_by",
            "visit_type",
            "chief_complaint",
            "status",
            "visit_date",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "status", "visit_date", "created_at"]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_department_display(self, obj):
        return dict(Department.CHOICES).get(obj.department, obj.department)

    def validate(self, attrs):
        doctor = attrs.get("attending_doctor")
        dept = attrs.get("department")
        if doctor is not None:
            if doctor.role != Role.DOCTOR:
                raise serializers.ValidationError(
                    {"attending_doctor": "Selected staff is not a doctor."}
                )
            if dept and doctor.department and doctor.department != dept:
                raise serializers.ValidationError(
                    {"attending_doctor": "Doctor belongs to a different department."}
                )
        return attrs


class VitalsSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(
        source="recorded_by.full_name", read_only=True
    )

    class Meta:
        model = Vitals
        fields = [
            "id",
            "encounter",
            "recorded_by",
            "recorded_by_name",
            "height_cm",
            "weight_kg",
            "bmi",
            "systolic_bp",
            "diastolic_bp",
            "pulse",
            "temperature_c",
            "spo2",
            "created_at",
        ]
        read_only_fields = ["id", "recorded_by", "bmi", "created_at"]

    def _range(self, attrs, field, lo, hi, label):
        val = attrs.get(field)
        if val is not None and (float(val) < lo or float(val) > hi):
            raise serializers.ValidationError(
                {field: f"{label} must be between {lo} and {hi}."}
            )

    def validate(self, attrs):
        self._range(attrs, "height_cm", 30, 250, "Height (cm)")
        self._range(attrs, "weight_kg", 1, 400, "Weight (kg)")
        self._range(attrs, "systolic_bp", 50, 300, "Systolic BP")
        self._range(attrs, "diastolic_bp", 30, 200, "Diastolic BP")
        self._range(attrs, "pulse", 20, 250, "Pulse")
        self._range(attrs, "temperature_c", 30, 45, "Temperature (°C)")
        self._range(attrs, "spo2", 50, 100, "SpO₂")
        sys_bp = attrs.get("systolic_bp")
        dia_bp = attrs.get("diastolic_bp")
        if sys_bp is not None and dia_bp is not None and dia_bp >= sys_bp:
            raise serializers.ValidationError(
                {"diastolic_bp": "Diastolic BP must be lower than systolic BP."}
            )
        return attrs


# --------------------------------------------------------------------------- #
# Lab: catalog, orders, reports, results
# --------------------------------------------------------------------------- #


class LabOrderSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    ordered_by_name = serializers.CharField(
        source="ordered_by.full_name", read_only=True
    )

    class Meta:
        model = LabOrder
        fields = [
            "id",
            "encounter",
            "patient",
            "patient_name",
            "ordered_by",
            "ordered_by_name",
            "test_code",
            "test_name",
            "category",
            "loinc_code",
            "status",
            "priority",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "ordered_by",
            "test_name",
            "category",
            "loinc_code",
            "status",
            "created_at",
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def validate_test_code(self, value):
        if not LabTestCatalog.is_valid(value):
            raise serializers.ValidationError("Unknown lab test code.")
        return value


class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = [
            "id",
            "lab_report",
            "patient",
            "test_code",
            "test_name",
            "category",
            "result_type",
            "loinc_code",
            "result_value",
            "result_unit",
            "reference_low",
            "reference_high",
            "flag",
            "report_text",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "lab_report",
            "patient",
            "test_name",
            "category",
            "result_type",
            "loinc_code",
            "result_unit",
            "reference_low",
            "reference_high",
            "flag",
            "created_at",
        ]

    def validate_test_code(self, value):
        if not LabTestCatalog.is_valid(value):
            raise serializers.ValidationError("Unknown lab test code.")
        return value

    def validate(self, attrs):
        meta = LabTestCatalog.get(attrs.get("test_code"))

        if not meta:
            return attrs
        if meta["type"] == LabResultType.QUANTITATIVE:
            val = attrs.get("result_value")
            if val is None:
                raise serializers.ValidationError(
                    {"result_value": "A numeric result is required for this test."}
                )
            if float(val) < 0:
                raise serializers.ValidationError(
                    {"result_value": "Result cannot be negative."}
                )
        else:
            if not (attrs.get("report_text") or "").strip():
                raise serializers.ValidationError(
                    {"report_text": "A report/conclusion is required for this test."}
                )
        return attrs


class LabReportSerializer(serializers.ModelSerializer):
    """A lab submission: order reference + one or more results (nested write)."""

    results = LabResultSerializer(many=True)
    entered_by_name = serializers.CharField(
        source="entered_by.full_name", read_only=True
    )

    class Meta:
        model = LabReport
        fields = [
            "id",
            "lab_order",
            "patient",
            "entered_by",
            "entered_by_name",
            "pdf_file",
            "source",
            "status",
            "results",
            "created_at",
        ]
        read_only_fields = ["id", "patient", "entered_by", "status", "created_at"]


# --------------------------------------------------------------------------- #
# Prescription & Diagnosis
# --------------------------------------------------------------------------- #


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    prescribed_by_name = serializers.CharField(
        source="prescribed_by.full_name", read_only=True
    )

    class Meta:
        model = Prescription
        fields = [
            "id",
            "encounter",
            "patient",
            "patient_name",
            "medication_name",
            "dosage_instruction",
            "status",
            "prescribed_by",
            "prescribed_by_name",
            "fulfilled_by",
            "fulfilled_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "prescribed_by",
            "fulfilled_by",
            "fulfilled_at",
            "created_at",
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class DiagnosisSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField(read_only=True)
    diagnosed_by_name = serializers.CharField(
        source="diagnosed_by.full_name", read_only=True
    )

    class Meta:
        model = Diagnosis
        fields = [
            "id",
            "encounter",
            "patient",
            "patient_name",
            "icd10_code",
            "disease_name",
            "clinical_status",
            "onset_date",
            "notes",
            "diagnosed_by",
            "diagnosed_by_name",
            "resolved_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "disease_name",
            "clinical_status",
            "diagnosed_by",
            "resolved_at",
            "created_at",
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def validate_icd10_code(self, value):
        if not ICD10.is_valid(value):
            raise serializers.ValidationError(
                f"'{value}' is not a recognised ICD-10 code in the supported list."
            )
        return value


# --------------------------------------------------------------------------- #
# Access requests (cross-hospital sharing)
# --------------------------------------------------------------------------- #


class AccessRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "national_id",
            "requester_label",
            "status",
            "expires_at",
            "approved_at",
            "created_at",
        ]
        read_only_fields = ["id", "status", "expires_at", "approved_at", "created_at"]


# --------------------------------------------------------------------------- #
# Password reset
# --------------------------------------------------------------------------- #


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = Staff.objects.get(pk=uid, is_active=True)
        except (Staff.DoesNotExist, ValueError, TypeError, OverflowError):
            raise ValidationError("Invalid reset link.")

        if not default_token_generator.check_token(user, attrs["token"]):
            raise ValidationError("Invalid or expired reset link.")

        attrs["user"] = user
        return attrs
