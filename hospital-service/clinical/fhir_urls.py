from django.urls import path

from . import fhir_views

urlpatterns = [
    path("Patient", fhir_views.patient_search),
    path("Encounter", fhir_views.encounter_search),
    path("Condition", fhir_views.condition_search),
    path("Observation", fhir_views.observation_search),
    path("$everything", fhir_views.patient_everything),
]
