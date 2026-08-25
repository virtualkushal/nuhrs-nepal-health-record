from django.urls import path

from . import views

urlpatterns = [
    # auth
    path("auth/login/", views.LoginView.as_view()),
    path("auth/refresh/", views.CookieTokenRefreshView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("auth/csrf/", views.CsrfView.as_view()),
    path("auth/change-password/", views.ChangePasswordView.as_view()),
    path("auth/me/", views.me),

    # single sign-on (seamless doctor handoff from a trusted facility)
    path("auth/sso-exchange/", views.SSOExchangeView.as_view()),
    path("auth/sso-verify/", views.SSOVerifyView.as_view()),


    # organizations
    path("orgs/", views.OrganizationListView.as_view()),
    path("orgs/active/", views.ActiveOrganizationsView.as_view()),
    path("orgs/register/", views.OrganizationRegisterView.as_view()),
    path("orgs/<int:pk>/approve/", views.OrganizationApproveView.as_view()),
    path("orgs/<int:pk>/reject/", views.OrganizationRejectView.as_view()),
    path("orgs/<int:pk>/suspend/", views.OrganizationSuspendView.as_view()),
    path("orgs/<int:pk>/reactivate/", views.OrganizationReactivateView.as_view()),

    # staff
    path("staff/", views.StaffView.as_view()),

    # ministry user management
    path("users/", views.AllUsersView.as_view()),
    path("users/<int:user_id>/reset-password/", views.AdminResetPasswordView.as_view()),

    # ministry accounts (super admin creates/lists/deletes Ministry officials)
    path("ministry-users/", views.MinistryUserView.as_view()),
    path("ministry-users/<int:pk>/", views.MinistryUserDetailView.as_view()),

    # exchange engine
    path("patients/<str:nid>/", views.PatientLookupView.as_view()),
    path("patients/<str:nid>/index/", views.PatientIndexView.as_view()),
    path("patients/<str:nid>/fetch/", views.PatientFetchView.as_view()),

    # patient portal
    path("patient/activate/", views.PatientActivateView.as_view()),
    path("patient/register/", views.PatientRegisterView.as_view()),
    path("patient/records/", views.PatientMyRecordsView.as_view()),
    path("patient/bundle/", views.PatientMyBundleView.as_view()),

    # national announcements
    path("announcements/", views.AnnouncementListCreateView.as_view()),
    path("announcements/<int:pk>/", views.AnnouncementDetailView.as_view()),

    # metadata ingest (from hospitals/labs)
    path("index/", views.IndexIngestView.as_view()),

    # audit & analytics
    path("audit/", views.AuditLogView.as_view()),
    path("analytics/summary/", views.AnalyticsSummaryView.as_view()),
]
