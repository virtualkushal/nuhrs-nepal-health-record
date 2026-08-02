from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AccessRequest,
    Diagnosis,
    Encounter,
    LabOrder,
    LabReport,
    LabResult,
    Patient,
    Prescription,
    Staff,
    Vitals,
)


@admin.register(Staff)
class StaffAdmin(UserAdmin):
    list_display = ("email", "full_name", "role", "department", "status", "is_active", "created_at")
    list_filter = ("role", "department", "status", "is_active")
    search_fields = ("email", "full_name")
    ordering = ("-created_at",)
    # Custom user model logs in by email; rebuild fieldsets around that.
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role", "department")}),
        ("Status", {"fields": ("status", "must_change_password", "is_active")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "department", "password1", "password2"),
            },
        ),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "hospital_identifier",
        "first_name",
        "last_name",
        "national_id",
        "gender",
        "blood_group",
        "registered_by",
        "created_at",
    )
    search_fields = ("hospital_identifier", "national_id", "first_name", "last_name", "phone_number")
    list_filter = ("gender", "blood_group", "registered_by")


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ("patient", "department", "attending_doctor", "status", "visit_type", "visit_date")
    list_filter = ("department", "status", "visit_type")


@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = ("encounter", "recorded_by", "bmi", "systolic_bp", "diastolic_bp", "pulse", "created_at")


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ("test_name", "patient", "category", "status", "priority", "created_at")
    list_filter = ("category", "status", "priority")


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ("lab_order", "patient", "entered_by", "source", "status", "created_at")
    list_filter = ("source", "status")


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("test_name", "patient", "result_type", "result_value", "result_unit", "flag", "created_at")
    list_filter = ("category", "result_type", "flag")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("medication_name", "patient", "status", "prescribed_by", "created_at")
    list_filter = ("status",)
    search_fields = ("medication_name",)


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ("icd10_code", "disease_name", "patient", "clinical_status", "created_at")
    list_filter = ("clinical_status",)
    search_fields = ("icd10_code", "disease_name")


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ("national_id", "requester_label", "status", "expires_at", "created_at")
    list_filter = ("status",)
