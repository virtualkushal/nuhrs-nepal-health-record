from django.urls import path

from . import fhir_views

urlpatterns = [
    path("Patient", fhir_views.patient_search),
    path("Encounter", fhir_views.encounter_search),
    path("Condition", fhir_views.condition_search),
    path("Observation", fhir_views.observation_search),
    path("AllergyIntolerance", fhir_views.allergy_search),
    path("MedicationRequest", fhir_views.medication_search),
    path("DiagnosticReport", fhir_views.diagnostic_report_search),
    path("$everything", fhir_views.patient_everything),
]
