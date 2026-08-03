"""
NUHRS federation FHIR routes for SwasthyaEHR (HOSP003).

Mounted under /fhir/ in config/urls.py. These NID-keyed, X-API-Key guarded
endpoints are called by the National Platform's RoutingEngine to fetch this
hospital's clinical data on demand. They mirror
hospital-service/clinical/fhir_urls.py so the whole federation speaks one shape.
"""

from django.urls import path

from . import nuhrs_adapter

urlpatterns = [
    path("Patient", nuhrs_adapter.patient_search),
    path("Encounter", nuhrs_adapter.encounter_search),
    path("Condition", nuhrs_adapter.condition_search),
    path("Observation", nuhrs_adapter.observation_search),
    path("MedicationRequest", nuhrs_adapter.medicationrequest_search),
    path("$everything", nuhrs_adapter.patient_everything),
]
