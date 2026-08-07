"""
HL7 FHIR R4 adapter for Pathlabs Nepal.

Maps variant B local columns (given_name/surname, test_panel, test_name/value/
uom/normal_range) into standardized FHIR DiagnosticReport + Observation
resources — IDENTICAL in shape to Central Diagnostic's output, despite the
different underlying column names and database (MySQL vs Postgres):
  - LOINC-coded Observations (code.coding with system/code/display)
  - Numeric valueQuantity with UCUM units
  - Structured referenceRange (low/high numeric values)
  - Auto-computed interpretation flags (H/L/N)
  - Qualitative tests use valueString (report-type)
  - LOINC-coded panel at the DiagnosticReport level

The catalog (lab.catalog) is the single source of truth for LOINC codes, units,
and reference ranges — shared verbatim with Central Diagnostic.
"""
from django.conf import settings

from . import catalog

NID_SYSTEM = settings.NID_SYSTEM
ORG_NAME = settings.ORG_NAME


def _subject(nid):
    return {"identifier": {"system": NID_SYSTEM, "value": nid}}


def to_fhir_patient(p):
    return {
        "resourceType": "Patient",
        "id": str(p.id),
        "identifier": [{"system": NID_SYSTEM, "value": p.nid}],
        "name": [{"text": f"{p.given_name} {p.surname}".strip()}],
        "gender": (p.gender or "").lower() or "unknown",
        "birthDate": p.dob.isoformat() if p.dob else None,
        "_source": ORG_NAME,
    }


def _parse_float(val):
    """Parse a string as float, return None if not numeric."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _interpretation(value_num, low, high):
    """Return FHIR interpretation code (H/L/N) based on numeric value vs range."""
    if value_num is None or (low is None and high is None):
        return None
    if low is not None and value_num < low:
        return {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": "L", "display": "Low"}]}
    if high is not None and value_num > high:
        return {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                            "code": "H", "display": "High"}]}
    return {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "N", "display": "Normal"}]}


def _result_observation(res):
    """
    Build a FHIR Observation for one LabResult line (variant B: test_name/value/uom).

    Uses the catalog to supply LOINC coding, UCUM unit, reference range, and
    auto-computes interpretation. Qualitative tests (e.g., serology) use valueString.
    """
    analyte_name = res.test_name
    meta = catalog.analyte_meta(analyte_name)

    loinc_tuple = meta.get("loinc", ("", ""))
    code_obj = {
        "coding": [{"system": "http://loinc.org", "code": loinc_tuple[0], "display": loinc_tuple[1]}] if loinc_tuple[0] else [],
        "text": analyte_name,
    }

    obs = {
        "resourceType": "Observation",
        "status": "final",
        "code": code_obj,
    }

    if catalog.is_qualitative(analyte_name):
        obs["valueString"] = res.value or "See report."
    else:
        value_num = _parse_float(res.value)
        unit = meta.get("unit", res.uom or "")

        if value_num is not None:
            obs["valueQuantity"] = {
                "value": value_num,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
                "code": unit,
            }
        else:
            obs["valueString"] = res.value or ""

        low = meta.get("low")
        high = meta.get("high")
        if low is not None or high is not None:
            range_obj = {}
            if low is not None:
                range_obj["low"] = {"value": low, "unit": unit}
            if high is not None:
                range_obj["high"] = {"value": high, "unit": unit}
            obs["referenceRange"] = [range_obj]

        interp = _interpretation(value_num, low, high)
        if interp:
            obs["interpretation"] = [interp]

    return obs


def to_fhir_diagnostic_report(r):
    """
    Build a FHIR DiagnosticReport for one LabReport panel (variant B columns).

    The DiagnosticReport gets a LOINC panel code from the catalog, and contained
    Observations are built from each LabResult line.
    """
    panel_name = r.test_panel
    panel_meta = catalog.panel_meta(panel_name)
    panel_loinc = panel_meta.get("loinc", ("", ""))

    code_obj = {
        "coding": [{"system": "http://loinc.org", "code": panel_loinc[0], "display": panel_loinc[1]}] if panel_loinc[0] else [],
        "text": panel_name,
    }

    contained = []
    for i, res in enumerate(r.results.all()):
        obs = _result_observation(res)
        obs["id"] = f"obs-{i}"
        contained.append(obs)

    return {
        "resourceType": "DiagnosticReport",
        "id": str(r.id),
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "LAB"}]}],
        "code": code_obj,
        "subject": _subject(r.patient.nid),
        "effectiveDateTime": r.reported_on.isoformat() if r.reported_on else None,
        "conclusion": r.interpretation or "",
        "performer": [{"display": ORG_NAME}],
        "resultsInterpreter": [{"display": r.referred_by}] if r.referred_by else [],
        "contained": contained,
        "result": [{"reference": f"#obs-{i}"} for i in range(len(contained))],
        "_source": ORG_NAME,
    }


def make_bundle(resources):
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resources),
        "entry": [{"resource": r} for r in resources],
    }
