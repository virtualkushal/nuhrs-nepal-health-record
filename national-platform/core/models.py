"""
NUHRS National Platform data models.

IMPORTANT: There are NO clinical tables here. The platform stores only
metadata — patient identity (MPI), the provider registry, a record index
(pointers to where clinical data lives), and audit logs.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Organization(models.Model):
    """Provider Registry entry for a hospital or laboratory."""

    class OrgType(models.TextChoices):
        HOSPITAL = "HOSPITAL", "Hospital"
        LAB = "LAB", "Laboratory"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        REJECTED = "REJECTED", "Rejected"

    organization_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    organization_name = models.CharField(max_length=200)
    organization_type = models.CharField(max_length=10, choices=OrgType.choices)
    license_number = models.CharField(max_length=100)
    api_base_url = models.URLField(help_text="Base URL of the org FHIR adapter, e.g. http://mediciti-hospital:8003/fhir")
    api_key = models.CharField(max_length=128, null=True, blank=True, help_text="Service-to-service key")
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255, blank=True)
    district = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organization_name} ({self.status})"


class PatientIdentity(models.Model):
    """Master Patient Index (MPI). Minimal identity only — NO clinical data."""

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    nid = models.CharField(max_length=20, unique=True, db_index=True)
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} [{self.nid}]"


class Announcement(models.Model):
    """Ministry-authored health announcements displayed to patients."""

    class Category(models.TextChoices):
        VACCINATION_DRIVE = "VACCINATION_DRIVE", "Vaccination Drive"
        SYSTEM_UPDATE = "SYSTEM_UPDATE", "System Update"
        PUBLIC_HEALTH = "PUBLIC_HEALTH", "Public Health"
        GENERAL = "GENERAL", "General"

    title = models.CharField(max_length=200)
    body = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)
    # String ref — the User model is defined further down this file; a direct
    # class reference here would NameError at import time.
    author = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="announcements")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return f"{self.title} ({self.category})"


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        if not username:
            raise ValueError("Username is required")
        user = self.model(username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra):
        extra.setdefault("role", User.Role.SUPER_ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("must_change_password", False)
        return self.create_user(username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Platform user. Doctors, lab techs, org admins, super admin, patients."""

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN", "Organization Admin"
        DOCTOR = "DOCTOR", "Doctor"
        LAB_TECHNICIAN = "LAB_TECHNICIAN", "Lab Technician"
        PATIENT = "PATIENT", "Patient"

    username = models.CharField(max_length=100, unique=True)
    # Human-friendly login name typed by the user. For staff it only needs to be
    # unique *within* their organization (enforced by unique_together below), so
    # two different hospitals can both have a doctor called "ramesh". For super
    # admin / patients this mirrors the username.
    login_name = models.CharField(max_length=100, blank=True)
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    organization = models.ForeignKey(
        Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name="staff"
    )
    patient_identity = models.OneToOneField(
        PatientIdentity, null=True, blank=True, on_delete=models.SET_NULL, related_name="user_account"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "username"

    class Meta:
        unique_together = [("organization", "login_name")]

    def __str__(self):
        return f"{self.username} ({self.role})"


class RecordIndex(models.Model):
    """
    The federation core: a pointer to a clinical record that lives inside an
    organization. The platform stores metadata only, never the record itself.
    """

    class ResourceType(models.TextChoices):
        ENCOUNTER = "Encounter", "Encounter"
        CONDITION = "Condition", "Condition"
        OBSERVATION = "Observation", "Observation"
        DIAGNOSTIC_REPORT = "DiagnosticReport", "DiagnosticReport"

    patient = models.ForeignKey(
        PatientIdentity, to_field="nid", db_column="nid",
        on_delete=models.CASCADE, related_name="records"
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="records")
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    local_record_id = models.CharField(max_length=64, help_text="Record ID inside the owning org")
    service_date = models.DateField()
    summary = models.CharField(max_length=255, help_text="Short human hint, e.g. 'Type 2 Diabetes'")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-service_date"]

    def __str__(self):
        return f"{self.resource_type} @ {self.organization.organization_name} ({self.service_date})"


class AuditLog(models.Model):
    """Immutable record of every access. This is the accountability mechanism."""

    class Action(models.TextChoices):
        SEARCH = "SEARCH", "Search"
        FETCH_ALL = "FETCH_ALL", "Fetch All"
        FETCH_ONE = "FETCH_ONE", "Fetch One"

    actor_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="audit_entries")
    actor_org = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    nid = models.CharField(max_length=20, db_index=True)
    record_index = models.ForeignKey(RecordIndex, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=12, choices=Action.choices)
    target_orgs = models.CharField(max_length=255, blank=True, help_text="Orgs contacted (comma separated)")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp} {self.action} {self.nid}"
