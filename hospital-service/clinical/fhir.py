"""
HL7 FHIR R4 adapter for the hospital service.

Reads local models (respecting the configured SCHEMA_VARIANT) and emits
standardized FHIR resources. This is where heterogeneous local schemas are
normalized into identical FHIR output.
"""
from django.conf import settings

NID_SYSTEM = settings.NID_SYSTEM
VARIANT = settings.SCHEMA_VARIANT


def _subject(nid):
    return {"identifier": {"system": NID_SYSTEM, "value": nid}}


# ---------------------------------------------------------------------------
# Variant-aware field readers
# ---------------------------------------------------------------------------
def patient_name(p):
    if VARIANT == "B":
        return f"{p.first_name} {p.last_name}".strip()
    return p.full_name


def encounter_fields(e):
    if VARIANT == "B":
        return {"clinician": e.physician, "date": e.visit_date, "category": e.visit_category, "reason": e.chief_complaint}
    return {"clinician": e.doctor_name, "date": e.encounter_date, "category": e.encounter_type, "reason": e.reason}


def condition_fields(c):
    if VARIANT == "B":
        return {"text": c.condition_desc, "code": c.icd_code, "status": c.status, "onset": c.onset}
    return {"text": c.diagnosis_text, "code": c.icd10_code, "status": c.clinical_status, "onset": c.onset_date}


def observation_fields(o):
    if VARIANT == "B":
        return {"name": o.measurement_name, "value": o.measurement_value, "unit": o.measurement_unit, "date": o.taken_on}
    return {"name": o.obs_type, "value": o.value, "unit": o.unit, "date": o.observed_date}


# ---------------------------------------------------------------------------
# FHIR resource builders
# ---------------------------------------------------------------------------
def to_fhir_patient(p):
    return {
        "resourceType": "Patient",
        "id": str(p.id),
        "identifier": [{"system": NID_SYSTEM, "value": p.nid}],
        "name": [{"text": patient_name(p)}],
        "gender": (p.gender or "").lower() or "unknown",
        "birthDate": p.dob.isoformat() if p.dob else None,
        "telecom": [{"system": "phone", "value": p.phone}] if p.phone else [],
        "_source": settings.ORG_NAME,
    }


def to_fhir_encounter(e):
    f = encounter_fields(e)
    return {
        "resourceType": "Encounter",
        "id": str(e.id),
        "status": "finished",
        "class": {"code": f["category"] or "AMB"},
        "subject": _subject(e.patient.nid),
        "period": {"start": f["date"].isoformat() if f["date"] else None},
        "reasonCode": [{"text": f["reason"]}] if f["reason"] else [],
        "participant": [{"individual": {"display": f["clinician"]}}] if f["clinician"] else [],
        "_source": settings.ORG_NAME,
    }


def to_fhir_condition(c):
    f = condition_fields(c)
    return {
        "resourceType": "Condition",
        "id": str(c.id),
        "subject": _subject(c.patient.nid),
        "code": {
            "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": f["code"], "display": f["text"]}],
            "text": f["text"],
        },
        "clinicalStatus": {"coding": [{"code": (f["status"] or "active").lower()}]},
        "onsetDateTime": f["onset"].isoformat() if f["onset"] else None,
        "_source": settings.ORG_NAME,
    }


def to_fhir_observation(o):
    f = observation_fields(o)
    return {
        "resourceType": "Observation",
        "id": str(o.id),
        "status": "final",
        "subject": _subject(o.patient.nid),
        "code": {"text": f["name"]},
        "valueQuantity": {"value": f["value"], "unit": f["unit"]},
        "effectiveDateTime": f["date"].isoformat() if f["date"] else None,
        "_source": settings.ORG_NAME,
    }


def make_bundle(resources):
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resources),
        "entry": [{"resource": r} for r in resources],
    }
