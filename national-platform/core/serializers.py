import re

from rest_framework import serializers

from .models import Announcement, AuditLog, Organization, PatientIdentity, RecordIndex, User
from .validators import validate_nid, validate_phone

# Accepts http(s) URLs whose host may be a Docker service name (dot-less),
# localhost, an IP, or a normal domain - e.g. http://new-hospital:8005/fhir.
# Django's built-in URLField validation rejects dot-less hostnames, which is
# exactly what every compose-network base URL looks like.
SERVICE_URL_RE = re.compile(
    r"^https?://[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?(?::\d{1,5})?(?:/\S*)?$"
)


def validate_service_url(value):
    value = (value or "").strip()
    if not SERVICE_URL_RE.match(value):
        raise serializers.ValidationError(
            "Enter a valid URL (e.g. http://mediciti-hospital:8003/fhir)."
        )
    return value


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id", "organization_code", "organization_name", "organization_type",
            "license_number", "api_base_url", "contact_email", "contact_phone",
            "address", "district", "province", "status", "created_at",
        ]
        read_only_fields = ["organization_code", "status", "created_at"]


class OrganizationRegisterSerializer(serializers.ModelSerializer):
    """Public registration submission — no code/api_key/status set by client."""

    # CharField + custom validator instead of the model's URLField, so
    # Docker-network hostnames (http://new-hospital:8005/fhir) pass.
    api_base_url = serializers.CharField(validators=[validate_service_url])

    class Meta:
        model = Organization
        fields = [
            "organization_name", "organization_type", "license_number",
            "api_base_url", "contact_email", "contact_phone", "address",
            "district", "province",
        ]


class PatientIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientIdentity
        fields = ["nid", "full_name", "date_of_birth", "gender", "phone", "email"]

    def validate_nid(self, value):
        return validate_nid(value)

    def validate_phone(self, value):
        # Optional field: only validate/normalize when a value was supplied.
        if not (value or "").strip():
            return ""
        return validate_phone(value)


class RecordIndexSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.organization_name", read_only=True)
    organization_type = serializers.CharField(source="organization.organization_type", read_only=True)

    class Meta:
        model = RecordIndex
        fields = [
            "id", "resource_type", "local_record_id", "service_date", "summary",
            "organization", "organization_name", "organization_type", "created_at",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor_user.username", read_only=True)
    actor_org_name = serializers.CharField(source="actor_org.organization_name", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "actor_username", "actor_org_name", "nid", "action",
            "target_orgs", "ip_address", "timestamp",
        ]


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "login_name", "full_name", "email", "phone", "role", "is_active"]
        read_only_fields = ["id", "username", "login_name"]


class UserProfileSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.organization_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "login_name", "full_name", "email", "role",
            "organization", "organization_name", "must_change_password",
            "is_active",
        ]


class AnnouncementSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)

    class Meta:
        model = Announcement
        fields = [
            "id", "title", "body", "category", "is_published",
            "published_at", "author", "author_name", "created_at", "updated_at",
        ]
        read_only_fields = ["author", "created_at", "updated_at"]
