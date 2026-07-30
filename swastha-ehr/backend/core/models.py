"""
Database models for SwasthyaEHR (v2 — multi-department OPD).

These mirror docs/DATABASE_SCHEMA.md exactly. Every table uses a UUID primary
key and created_at/updated_at timestamps. Login is by email for everyone.
"""

import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.indexes import GinIndex
from django.db import models, transaction

from .constants import (
    AccessRequestStatus,
    BloodGroup,
    Department,
    DiagnosisStatus,
    EncounterStatus,
    Gender,
    ICD10,
    LabCategory,
    LabOrderPriority,
    LabOrderStatus,
    LabResultSource,
    LabResultType,
    LabTestCatalog,
    MaritalStatus,
    PrescriptionStatus,
    RegisteredBy,
    ResultFlag,
    Role,
    StaffStatus,
    VisitType,
)


class TimeStampedUUIDModel(models.Model):
    """Abstract base: UUID primary key + auto timestamps for every table."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class StaffManager(BaseUserManager):
    """User manager keyed on email instead of username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        # username kept for Django internals; derive from email.
        extra.setdefault("username", email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.ADMIN)
        extra.setdefault("status", StaffStatus.ACTIVE)
        extra.setdefault("must_change_password", False)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra)


class Staff(AbstractUser):
    """
    Custom user model = every login account. Login is by EMAIL.

    Staff self-register (status=PENDING) and an admin approves them
    (status=ACTIVE). Patients also get an account. `role` lives on the user so
    JWT can read it directly.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # email is the login identifier — unique + required.
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.CHOICES)
    department = models.CharField(
        max_length=30, choices=Department.CHOICES, blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=StaffStatus.CHOICES, default=StaffStatus.PENDING
    )
    must_change_password = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = StaffManager()

    class Meta:
        db_table = "core_staff"

    def __str__(self):
        return f"{self.full_name or self.email} ({self.role})"

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class Patient(TimeStampedUUIDModel):
    """Patient demographics, NID, blood group, free-text allergies."""

    user = models.OneToOneField(
        "Staff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_profile",
    )
    hospital_identifier = models.CharField(max_length=20, unique=True, editable=False)
    national_id = models.CharField(max_length=20, unique=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.CHOICES)
    blood_group = models.CharField(
        max_length=10, choices=BloodGroup.CHOICES, default="UNKNOWN"
    )
    allergies = models.JSONField(default=list, blank=True)

    address = models.CharField(max_length=255, blank=True)
    emergency_contact_name = models.CharField(max_length=120, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    marital_status = models.CharField(
        max_length=20, choices=MaritalStatus.CHOICES, blank=True
    )
    occupation = models.CharField(max_length=120, blank=True)

    registered_by = models.CharField(max_length=20, choices=RegisteredBy.CHOICES)

    class Meta:
        db_table = "core_patient"
        indexes = [GinIndex(fields=["allergies"], name="patient_allergies_gin")]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.hospital_identifier})"

    def save(self, *args, **kwargs):
        if not self.hospital_identifier:
            self.hospital_identifier = self._generate_hospital_identifier()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_hospital_identifier():
        from django.utils import timezone

        year = timezone.now().year
        prefix = f"HOSP-{year}-"
        with transaction.atomic():
            last = (
                Patient.objects.select_for_update()
                .filter(hospital_identifier__startswith=prefix)
                .order_by("-hospital_identifier")
                .first()
            )
            next_seq = 1
            if last:
                try:
                    next_seq = int(last.hospital_identifier.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    next_seq = 1
            return f"{prefix}{next_seq:05d}"


class Encounter(TimeStampedUUIDModel):
    """One OPD visit — the backbone tying vitals, diagnoses, orders, rx together."""

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="encounters"
    )
    department = models.CharField(max_length=30, choices=Department.CHOICES)
    attending_doctor = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attending_encounters",
    )
    created_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="created_encounters"
    )
    visit_type = models.CharField(
        max_length=10, choices=VisitType.CHOICES, default=VisitType.NEW
    )
    chief_complaint = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=EncounterStatus.CHOICES, default=EncounterStatus.REGISTERED
    )
    visit_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "core_encounter"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient} — {self.department} [{self.status}]"


class Vitals(TimeStampedUUIDModel):
    """Vitals recorded by a nurse for an encounter (one-to-one)."""

    encounter = models.OneToOneField(
        Encounter, on_delete=models.CASCADE, related_name="vitals"
    )
    recorded_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="recorded_vitals"
    )
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    systolic_bp = models.PositiveIntegerField(null=True, blank=True)
    diastolic_bp = models.PositiveIntegerField(null=True, blank=True)
    pulse = models.PositiveIntegerField(null=True, blank=True)
    temperature_c = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    spo2 = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "core_vitals"

    def save(self, *args, **kwargs):
        # BMI computed server-side; never trusted from the client.
        if self.height_cm and self.weight_kg and float(self.height_cm) > 0:
            h_m = float(self.height_cm) / 100.0
            self.bmi = round(float(self.weight_kg) / (h_m * h_m), 1)
        else:
            self.bmi = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vitals for {self.encounter}"


class LabOrder(TimeStampedUUIDModel):
    """A doctor's request for a catalog test (the lab's pending to-do)."""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="lab_orders"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="lab_orders"
    )
    ordered_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="ordered_lab_orders"
    )
    test_code = models.CharField(max_length=50)
    test_name = models.CharField(max_length=120, blank=True)
    category = models.CharField(max_length=20, choices=LabCategory.CHOICES, blank=True)
    loinc_code = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20, choices=LabOrderStatus.CHOICES, default=LabOrderStatus.PENDING
    )
    priority = models.CharField(
        max_length=10, choices=LabOrderPriority.CHOICES, default=LabOrderPriority.ROUTINE
    )

    class Meta:
        db_table = "core_laborder"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        meta = LabTestCatalog.get(self.test_code)
        if meta:
            self.test_name = meta["name"]
            self.category = meta["category"]
            self.loinc_code = meta.get("loinc", "")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.test_name} for {self.patient} [{self.status}]"


class LabReport(TimeStampedUUIDModel):
    """A lab tech's submission for an order: optional PDF + status."""

    UPLOADED = "UPLOADED"
    EXTRACTED = "EXTRACTED"
    CONFIRMED = "CONFIRMED"
    STATUS_CHOICES = [
        (UPLOADED, "Uploaded"),
        (EXTRACTED, "Extracted"),
        (CONFIRMED, "Confirmed"),
    ]

    lab_order = models.ForeignKey(
        LabOrder, on_delete=models.CASCADE, related_name="reports"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="lab_reports"
    )
    entered_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="entered_reports"
    )
    pdf_file = models.FileField(upload_to="lab_reports/", null=True, blank=True)
    source = models.CharField(
        max_length=20, choices=LabResultSource.CHOICES, default=LabResultSource.MANUAL
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=CONFIRMED)

    class Meta:
        db_table = "core_labreport"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report for {self.lab_order} [{self.status}]"


class LabResult(TimeStampedUUIDModel):
    """One test result (quantitative value+range+flag OR report text)."""

    lab_report = models.ForeignKey(
        LabReport, on_delete=models.CASCADE, related_name="results"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="lab_results"
    )
    test_code = models.CharField(max_length=50)
    test_name = models.CharField(max_length=120, blank=True)
    category = models.CharField(max_length=20, choices=LabCategory.CHOICES, blank=True)
    result_type = models.CharField(max_length=20, choices=LabResultType.CHOICES)
    loinc_code = models.CharField(max_length=20, blank=True)

    result_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    result_unit = models.CharField(max_length=20, blank=True)
    reference_low = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reference_high = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    flag = models.CharField(max_length=10, choices=ResultFlag.CHOICES, blank=True)

    report_text = models.CharField(max_length=1000, blank=True)

    class Meta:
        db_table = "core_labresult"
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        meta = LabTestCatalog.get(self.test_code)
        if meta:
            self.test_name = meta["name"]
            self.category = meta["category"]
            self.result_type = meta["type"]
            self.loinc_code = meta.get("loinc", "")
            if self.result_type == LabResultType.QUANTITATIVE:
                self.result_unit = meta.get("unit", "")
                self.reference_low = meta.get("low")
                self.reference_high = meta.get("high")
        # Auto-flag quantitative results vs reference range.
        if self.result_type == LabResultType.QUANTITATIVE and self.result_value is not None:
            val = float(self.result_value)
            low = float(self.reference_low) if self.reference_low is not None else None
            high = float(self.reference_high) if self.reference_high is not None else None
            if low is not None and val < low:
                self.flag = ResultFlag.LOW
            elif high is not None and val > high:
                self.flag = ResultFlag.HIGH
            else:
                self.flag = ResultFlag.NORMAL
        super().save(*args, **kwargs)

    def __str__(self):
        if self.result_type == LabResultType.QUANTITATIVE:
            return f"{self.test_name}={self.result_value}{self.result_unit} [{self.flag}]"
        return f"{self.test_name}: {self.report_text[:40]}"


class Prescription(TimeStampedUUIDModel):
    """A medication order written by a doctor, fulfilled by a pharmacist."""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="prescriptions"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="prescriptions"
    )
    prescribed_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="written_prescriptions"
    )
    fulfilled_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="fulfilled_prescriptions",
    )
    medication_name = models.CharField(max_length=200)
    dosage_instruction = models.CharField(max_length=500)
    status = models.CharField(
        max_length=20, choices=PrescriptionStatus.CHOICES, default=PrescriptionStatus.ACTIVE
    )
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "core_prescription"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.medication_name} for {self.patient} [{self.status}]"


class Diagnosis(TimeStampedUUIDModel):
    """An ICD-10 coded condition recorded by a doctor (the problem list)."""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="diagnoses"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="diagnoses"
    )
    diagnosed_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="recorded_diagnoses"
    )
    icd10_code = models.CharField(max_length=10, choices=ICD10.CHOICES)
    disease_name = models.CharField(max_length=255, blank=True)
    clinical_status = models.CharField(
        max_length=20, choices=DiagnosisStatus.CHOICES, default=DiagnosisStatus.ACTIVE
    )
    onset_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=1000, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "core_diagnosis"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.icd10_code and not self.disease_name:
            self.disease_name = ICD10.display(self.icd10_code)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.icd10_code} {self.disease_name} for {self.patient}"


class AccessRequest(TimeStampedUUIDModel):
    """Cross-hospital FHIR share request awaiting patient approval (no code)."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="access_requests",
    )
    national_id = models.CharField(max_length=20)
    requester_label = models.CharField(max_length=120, blank=True)
    requester_hospital = models.CharField(max_length=20, blank=True)
    # ["diagnoses","labs","medications"] or ["everything"]; empty == everything.
    scope = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20,
        choices=AccessRequestStatus.CHOICES,
        default=AccessRequestStatus.PENDING,
    )
    approved_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_share_requests",
    )
    expires_at = models.DateTimeField()
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "core_accessrequest"
        ordering = ["-created_at"]

    def __str__(self):
        return f"AccessRequest {self.national_id} [{self.status}]"


class OutboundShareRequest(TimeStampedUUIDModel):
    """A request THIS hospital sent to a PEER hospital for a patient's records."""

    requested_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="outbound_share_requests"
    )
    peer_code = models.CharField(max_length=20)
    peer_name = models.CharField(max_length=120, blank=True)
    peer_base_url = models.CharField(max_length=255)
    national_id = models.CharField(max_length=20)
    scope = models.JSONField(default=list, blank=True)
    # PENDING/APPROVED/DENIED/EXPIRED (mirrors peer) or ERROR if the call failed.
    status = models.CharField(max_length=20, default="PENDING")
    peer_request_id = models.CharField(max_length=64, blank=True)
    bundle = models.JSONField(null=True, blank=True)
    error = models.CharField(max_length=500, blank=True)
    imported = models.BooleanField(default=False)

    class Meta:
        db_table = "core_outbound_share_request"
        ordering = ["-created_at"]

    def __str__(self):
        return f"OutboundShare {self.national_id} -> {self.peer_code} [{self.status}]"


class ExternalRecord(TimeStampedUUIDModel):
    """A peer hospital's FHIR Bundle imported and saved into THIS hospital's DB."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="external_records",
    )
    national_id = models.CharField(max_length=20)
    source_hospital_code = models.CharField(max_length=20)
    source_hospital_name = models.CharField(max_length=120, blank=True)
    scope = models.JSONField(default=list, blank=True)
    bundle = models.JSONField()
    imported_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="imported_records"
    )

    class Meta:
        db_table = "core_external_record"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ExternalRecord {self.national_id} from {self.source_hospital_code}"
