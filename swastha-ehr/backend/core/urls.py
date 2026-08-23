from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from . import interop_views

app_name = "core"

urlpatterns = [
    # Liveness
    path("health/", views.health, name="health"),
    # Auth
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    path("auth/register/", views.StaffRegisterView.as_view(), name="staff_register"),
    path(
        "auth/change-password/",
        views.ChangePasswordView.as_view(),
        name="change_password",
    ),
    path(
        "auth/password-reset/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "auth/password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # Staff management + approval (ADMIN)
    path("auth/staff/", views.StaffListCreateView.as_view(), name="staff_list_create"),
    path("auth/staff/<uuid:pk>/", views.StaffDetailView.as_view(), name="staff_detail"),
    path(
        "auth/staff/<uuid:pk>/approve/",
        views.StaffApproveView.as_view(),
        name="staff_approve",
    ),
    path(
        "auth/staff/<uuid:pk>/reject/",
        views.StaffRejectView.as_view(),
        name="staff_reject",
    ),
    path("admin/overview/", views.AdminOverviewView.as_view(), name="admin_overview"),
    # NUHRS National Dashboard SSO launch (doctor only)
    path("nuhrs/launch/", views.NuhrsLaunchView.as_view(), name="nuhrs_launch"),

    # Reference catalogs
    path("departments/", views.departments_catalog, name="departments_catalog"),
    path("lab-catalog/", views.lab_catalog, name="lab_catalog"),
    path("icd10/", views.icd10_catalog, name="icd10_catalog"),
    # Patient registration & directory
    path(
        "patients/register/",
        views.PatientSelfRegisterView.as_view(),
        name="patient_self_register",
    ),
    path("patients/", views.PatientListCreateView.as_view(), name="patient_list_create"),
    path("patients/<uuid:pk>/", views.PatientDetailView.as_view(), name="patient_detail"),
    path(
        "patients/<uuid:pk>/timeline/",
        views.PatientTimelineView.as_view(),
        name="patient_timeline",
    ),
    # Patient portal + sharing decisions
    path("portal/me/", views.PatientPortalView.as_view(), name="patient_portal_me"),
    path(
        "portal/share-requests/",
        views.PatientShareRequestsView.as_view(),
        name="patient_share_requests",
    ),
    path(
        "portal/share-requests/<uuid:pk>/decision/",
        views.PatientShareDecisionView.as_view(),
        name="patient_share_decision",
    ),
    # Encounters + status queue
    path(
        "encounters/",
        views.EncounterListCreateView.as_view(),
        name="encounter_list_create",
    ),
    path(
        "encounters/<uuid:pk>/",
        views.EncounterDetailView.as_view(),
        name="encounter_detail",
    ),
    path(
        "encounters/<uuid:pk>/status/",
        views.EncounterStatusView.as_view(),
        name="encounter_status",
    ),
    # Vitals (nurse)
    path("vitals/", views.VitalsCreateView.as_view(), name="vitals_create"),
    path(
        "vitals/<uuid:encounter_id>/",
        views.VitalsDetailView.as_view(),
        name="vitals_detail",
    ),
    # Laboratory
    path(
        "lab-orders/",
        views.LabOrderListCreateView.as_view(),
        name="lab_order_list_create",
    ),
    path(
        "lab-reports/",
        views.LabReportCreateView.as_view(),
        name="lab_report_create",
    ),
    path(
        "lab-results/",
        views.LabResultListView.as_view(),
        name="lab_result_list",
    ),
    # Prescriptions
    path(
        "prescriptions/",
        views.PrescriptionCreateView.as_view(),
        name="prescription_create",
    ),
    path(
        "prescriptions/queue/",
        views.PrescriptionQueueView.as_view(),
        name="prescription_queue",
    ),
    path(
        "prescriptions/<uuid:pk>/fulfill/",
        views.PrescriptionFulfillView.as_view(),
        name="prescription_fulfill",
    ),
    # Diagnoses
    path(
        "diagnoses/",
        views.DiagnosisListCreateView.as_view(),
        name="diagnosis_list_create",
    ),
    path(
        "diagnoses/<uuid:pk>/resolve/",
        views.DiagnosisResolveView.as_view(),
        name="diagnosis_resolve",
    ),
    # Cross-hospital sharing (external hospital entry points)
    path(
        "share/request/",
        views.ShareRequestCreateView.as_view(),
        name="share_request_create",
    ),
    path(
        "share/request/<uuid:pk>/",
        views.ShareRequestStatusView.as_view(),
        name="share_request_status",
    ),
    # Cross-hospital interoperability (two-system FHIR sharing)
    path("hospitals/", interop_views.hospitals_registry, name="hospitals_registry"),
    path("share/outbound/", interop_views.OutboundShareCreateView.as_view(), name="share_outbound_create"),
    path("share/outbound/list/", interop_views.OutboundShareListView.as_view(), name="share_outbound_list"),
    path("share/outbound/<uuid:pk>/poll/", interop_views.OutboundSharePollView.as_view(), name="share_outbound_poll"),
    path("share/outbound/<uuid:pk>/import/", interop_views.OutboundShareImportView.as_view(), name="share_outbound_import"),
    path("admin/share-requests/", interop_views.AdminShareRequestsView.as_view(), name="admin_share_requests"),
    path("admin/share-requests/<uuid:pk>/decision/", interop_views.AdminShareDecisionView.as_view(), name="admin_share_decision"),
    path("share/external-records/", interop_views.ExternalRecordListView.as_view(), name="external_record_list"),
    path("share/external-records/<uuid:pk>/", interop_views.ExternalRecordDetailView.as_view(), name="external_record_detail"),
]
