"""
HL7 FHIR R4 adapter for the laboratory service.

Maps variant-specific local columns into standardized FHIR DiagnosticReport
resources (with contained result Observations).
"""
from django.conf import settings

from . import terminology

NID_SYSTEM = settings.NID_SYSTEM
VARIANT = settings.SCHEMA_VARIANT


def _subject(nid):
    return {"identifier": {"system": NID_SYSTEM, "value": nid}}


def patient_name(p):
    if VARIANT == "B":
        return f"{p.given_name} {p.surname}".strip()
    return p.patient_name


def report_fields(r):
    if VARIANT == "B":
        return {"panel": r.test_panel, "doctor": r.referred_by, "date": r.reported_on, "conclusion": r.interpretation}
    return {"panel": r.panel_name, "doctor": r.ordering_doctor, "date": r.report_date, "conclusion": r.conclusion}


def result_fields(res):
    if VARIANT == "B":
        return {"name": res.test_name, "value": res.value, "unit": res.uom, "range": res.normal_range}
    return {"name": res.analyte, "value": res.result_value, "unit": res.units, "range": res.reference_range}


def to_fhir_patient(p):
    return {
        "resourceType": "Patient",
        "id": str(p.id),
        "identifier": [{"system": NID_SYSTEM, "value": p.nid}],
        "name": [{"text": patient_name(p)}],
        "gender": (p.gender or "").lower() or "unknown",
        "birthDate": p.dob.isoformat() if p.dob else None,
        "_source": settings.ORG_NAME,
    }


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _result_observation(res, index):
    f = result_fields(res)
    value = _to_number(f["value"])
    loinc = terminology.observable_coding(f["name"])
    obs = {
        "resourceType": "Observation",
        "id": f"obs-{index}",
        "status": "final",
        "code": {"coding": [loinc] if loinc else [], "text": f["name"]},
        "referenceRange": [{"text": f["range"]}] if f["range"] else [],
    }
    if value is not None:
        obs["valueQuantity"] = {"value": value, "unit": f["unit"]}
    else:
        obs["valueString"] = str(f["value"])
    return obs


def to_fhir_diagnostic_report(r):
    f = report_fields(r)
    contained = [_result_observation(res, i) for i, res in enumerate(r.results.all())]
    panel = terminology.panel_coding(f["panel"])
    return {
        "resourceType": "DiagnosticReport",
        "id": str(r.id),
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "LAB"}]}],
        "code": {"coding": [panel] if panel else [], "text": f["panel"]},
        "subject": _subject(r.patient.nid),
        "effectiveDateTime": f["date"].isoformat() if f["date"] else None,
        "conclusion": f["conclusion"],
        "performer": [{"display": settings.ORG_NAME}],
        "resultsInterpreter": [{"display": f["doctor"]}] if f["doctor"] else [],
        "contained": contained,
        "result": [{"reference": f"#obs-{i}"} for i in range(len(contained))],
        "_source": settings.ORG_NAME,
    }


def make_bundle(resources):
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resources),
        "entry": [{"resource": r} for r in resources],
    }
