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

from core.models import Diagnosis, Encounter, LabReport, LabResult, Patient, Prescription, Vitals

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


def vitals_summary(vitals: Vitals) -> str:
    parts = []
    if vitals.systolic_bp and vitals.diastolic_bp:
        parts.append(f"BP {vitals.systolic_bp}/{vitals.diastolic_bp}")
    if vitals.pulse:
        parts.append(f"Pulse {vitals.pulse}")
    if vitals.temperature_c is not None:
        parts.append(f"Temp {vitals.temperature_c}")
    if vitals.spo2:
        parts.append(f"SpO2 {vitals.spo2}%")
    if vitals.height_cm is not None:
        parts.append(f"Ht {vitals.height_cm}cm")
    if vitals.weight_kg is not None:
        parts.append(f"Wt {vitals.weight_kg}kg")
    if vitals.bmi is not None:
        parts.append(f"BMI {vitals.bmi}")
    return " · ".join(parts)


def push_lab_report(report: LabReport) -> None:
    order = report.lab_order
    test_name = (order.test_name or order.test_code or "Laboratory test").strip()
    values = [
        f"{r.test_code}: {r.result_value}" if r.result_value is not None else f"{r.test_code}"
        for r in report.results.all()
    ]
    summary = f"{test_name} — {'; '.join(values)}" if values else f"{test_name} (report)"
    _push(
        report.patient,
        "DiagnosticReport",
        report.id,
        report.created_at.date(),
        summary[:255],
    )


def push_encounter(e) -> None:
    """Index a visit (Encounter) so it shows in the portal's visit lists."""
    from core.constants import Department

    dept = dict(Department.CHOICES).get(e.department, e.department)
    _push(
        e.patient,
        "Encounter",
        e.id,
        e.created_at.date(),
        f"Visit — {dept}",
    )


def push_vitals(v: Vitals) -> None:
    summary = vitals_summary(v)
    _push(
        v.encounter.patient,
        "Observation",
        v.id,
        v.created_at.date(),
        f"Vitals — {summary}" if summary else "Vitals",
    )


# -- bulk publishers (used by the management command) ------------------------

def push_patient_records(patient: Patient) -> None:
    """Index all records of one patient (used by --nid or startup push)."""
    for e in Encounter.objects.filter(patient=patient):
        push_encounter(e)
    for dx in Diagnosis.objects.filter(patient=patient):
        push_condition(dx)
    for res in LabResult.objects.filter(patient=patient):
        push_observation(res)
    for rx in Prescription.objects.filter(patient=patient):
        push_medication(rx)
    for rep in LabReport.objects.filter(patient=patient).select_related("lab_order"):
        push_lab_report(rep)
    for v in Vitals.objects.filter(encounter__patient=patient):
        push_vitals(v)