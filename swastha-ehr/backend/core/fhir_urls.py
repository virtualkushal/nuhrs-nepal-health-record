"""
Routes for the read-only HL7 FHIR R4 interoperability layer.

Mounted under /api/fhir/v1/ in config/urls.py.
"""

from django.urls import path

from . import views

app_name = "fhir"

urlpatterns = [
    path("Patient/<uuid:pk>/", views.FHIRPatientView.as_view(), name="fhir_patient"),
    path(
        "Patient/<uuid:pk>/$everything/",
        views.FHIRPatientEverythingView.as_view(),
        name="fhir_patient_everything",
    ),
    path(
        "Observation/<uuid:pk>/",
        views.FHIRObservationView.as_view(),
        name="fhir_observation",
    ),
    path(
        "Condition/<uuid:pk>/",
        views.FHIRConditionView.as_view(),
        name="fhir_condition",
    ),
]
