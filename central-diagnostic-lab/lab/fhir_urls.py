from django.urls import path

from . import fhir_views

urlpatterns = [
    path("Patient", fhir_views.patient_search),
    path("DiagnosticReport", fhir_views.diagnostic_report_search),
    path("$everything", fhir_views.patient_everything),
]
