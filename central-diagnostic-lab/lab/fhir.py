"""
HL7 FHIR R4 adapter for Central Diagnostic Laboratory.

Maps variant A local columns (patient_name, panel_name, analyte, result_value,
units, reference_range) into standardized FHIR DiagnosticReport + Observation
resources with:
  - LOINC-coded Observations (code.coding with system/code/display)
  - Numeric valueQuantity with UCUM units
  - Structured referenceRange (low/high numeric values)
  - Auto-computed interpretation flags (H/L/N)
  - Qualitative tests use valueString (report-type)
  - LOINC-coded panel at the DiagnosticReport level

The catalog (lab.catalog) is the single source of truth for LOINC codes, units,
and reference ranges.
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
        "name": [{"text": p.patient_name}],
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
    Build a FHIR Observation for one LabResult analyte line.
    
    Uses the catalog to supply LOINC coding, UCUM unit, reference range, and
    auto-computes interpretation. Qualitative tests (e.g., serology) use valueString.
    """
    analyte_name = res.analyte
    meta = catalog.analyte_meta(analyte_name)
    
    # LOINC code from catalog
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
    
    # Qualitative (report-type) vs quantitative
    if catalog.is_qualitative(analyte_name):
        # Report-type test: use valueString
        obs["valueString"] = res.result_value or "See report."
    else:
        # Quantitative: numeric valueQuantity + UCUM + referenceRange + interpretation
        value_num = _parse_float(res.result_value)
        unit = meta.get("unit", res.units or "")
        
        if value_num is not None:
            obs["valueQuantity"] = {
                "value": value_num,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
                "code": unit,
            }
        else:
            # Fallback if value not numeric
            obs["valueString"] = res.result_value or ""
        
        # Structured referenceRange from catalog
        low = meta.get("low")
        high = meta.get("high")
        if low is not None or high is not None:
            range_obj = {}
            if low is not None:
                range_obj["low"] = {"value": low, "unit": unit}
            if high is not None:
                range_obj["high"] = {"value": high, "unit": unit}
            obs["referenceRange"] = [range_obj]
        
        # Auto-interpret
        interp = _interpretation(value_num, low, high)
        if interp:
            obs["interpretation"] = [interp]
    
    return obs


def to_fhir_diagnostic_report(r):
    """
    Build a FHIR DiagnosticReport for one LabReport panel.
    
    The DiagnosticReport gets a LOINC panel code from the catalog, and contained
    Observations are built from each LabResult line.
    """
    panel_name = r.panel_name
    panel_meta = catalog.panel_meta(panel_name)
    panel_loinc = panel_meta.get("loinc", ("", ""))
    
    # DiagnosticReport.code with LOINC panel
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
        "effectiveDateTime": r.report_date.isoformat() if r.report_date else None,
        "conclusion": r.conclusion or "",
        "performer": [{"display": ORG_NAME}],
        "resultsInterpreter": [{"display": r.ordering_doctor}] if r.ordering_doctor else [],
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
