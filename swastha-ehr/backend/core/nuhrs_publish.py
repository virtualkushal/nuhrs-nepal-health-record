"""
Live publish client for the NUHRS federation (write side).

Pushes lightweight record metadata (NID + patient demographics + resource type
+ local UUID + one-line summary) to the National Platform index so newly
created SwasthyaEHR records become discoverable federation-wide immediately.

The real clinical data never leaves this instance; it is fetched back on demand
by the platform through core.nuhrs_adapter (the NID-keyed FHIR endpoints).

Used by:
  - the `nuhrs_push` management command (bulk / startup indexing)
  - core.signals (automatic indexing the moment a record is saved)
"""

import logging

import requests
from django.conf import settings

from core.models import Diagnosis, LabResult, Patient, Prescription

logger = logging.getLogger(__name__)


def _patient_meta(patient: Patient) -> dict:
    return {
        "nid": patient.national_id,
        "full_name": f"{patient.first_name} {patient.last_name}".strip(),
        "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
        "gender": (patient.gender or "OTHER").upper(),
        "phone": patient.phone_number or "",
    }


def _push(patient, resource_type: str, local_record_id, service_date, summary: str) -> None:
    """POST one metadata pointer to the national platform index. Swallows errors."""
    if not getattr(settings, "NUHRS_ENABLED", False):
        return
    if not patient or not patient.national_id:
        return

    payload = {
        "nid": patient.national_id,
        "patient": _patient_meta(patient),
        "resource_type": resource_type,
        "local_record_id": str(local_record_id),
        "service_date": str(service_date),
        "summary": summary,
    }
    url = f"{settings.NUHRS_PLATFORM_URL.rstrip('/')}/api/index/"
    try:
        requests.post(
            url,
            json=payload,
            headers={"X-API-Key": settings.NUHRS_API_KEY},
            timeout=10,
        ).raise_for_status()
    except requests.RequestException as exc:
        logger.warning("NUHRS index push failed for %s: %s", patient.national_id, exc)


# -- individual record publishers -------------------------------------------

def push_condition(dx: Diagnosis) -> None:
    summary = f"{dx.icd10_code}".strip()
    _push(dx.patient, "Condition", dx.id, dx.created_at.date(), summary or "Condition")


def push_observation(res: LabResult) -> None:
    value = res.result_value if res.result_value else (res.report_text or "")
    summary = f"{res.test_code}: {value}".strip().strip(":").strip()
    _push(res.patient, "Observation", res.id, res.created_at.date(), summary or "Observation")


def push_medication(rx: Prescription) -> None:
    summary = f"{rx.medication_name} - {rx.dosage_instruction}".rstrip(" -")
    _push(rx.patient, "MedicationRequest", rx.id, rx.created_at.date(), summary or "MedicationRequest")


# -- bulk publishers (used by the management command) ------------------------

def push_patient_records(patient: Patient) -> None:
    """Index all records of one patient (used by --nid or startup push)."""
    for dx in Diagnosis.objects.filter(patient=patient):
        push_condition(dx)
    for res in LabResult.objects.filter(patient=patient):
        push_observation(res)
    for rx in Prescription.objects.filter(patient=patient):
        push_medication(rx)