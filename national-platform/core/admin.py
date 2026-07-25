from django.contrib import admin

from .models import AuditLog, Organization, PatientIdentity, RecordIndex, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("organization_name", "organization_type", "organization_code", "status", "district")
    list_filter = ("organization_type", "status")
    search_fields = ("organization_name", "organization_code")


@admin.register(PatientIdentity)
class PatientIdentityAdmin(admin.ModelAdmin):
    list_display = ("nid", "full_name", "date_of_birth", "gender", "phone")
    search_fields = ("nid", "full_name")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "organization", "is_active", "must_change_password")
    list_filter = ("role", "is_active")
    search_fields = ("username", "full_name")


@admin.register(RecordIndex)
class RecordIndexAdmin(admin.ModelAdmin):
    list_display = ("patient", "resource_type", "organization", "service_date", "summary")
    list_filter = ("resource_type", "organization")
    search_fields = ("patient__nid", "summary")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "actor_user", "action", "nid", "target_orgs")
    list_filter = ("action",)
    search_fields = ("nid",)
