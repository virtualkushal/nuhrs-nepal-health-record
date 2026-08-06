from rest_framework import serializers

from .models import Announcement, AuditLog, Organization, PatientIdentity, RecordIndex, User


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
