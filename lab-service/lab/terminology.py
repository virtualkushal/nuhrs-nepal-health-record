"""
Canonical LOINC terminology for the NUHRS federation.

Purpose: guarantee that "similar" test names / LOINC codes map to the SAME
standardised FHIR coding across every facility, so the National Platform sees
one observational series for one measurable property (trends, dedupe,
analytics) no matter how the source system named it.

Rules enforced here:
  * One measurable property = one canonical LOINC code (single entry).
  * A local alias/synonym maps to exactly ONE canonical LOINC code.
  * A value that already looks like a LOINC code (NNNNN-N) passes through.

Consistency check:  python manage.py check_terminology
"""
import re

LOINC = "http://loinc.org"

LOINC_CODE_RE = re.compile(r"^\d{2,6}-\d$")


def normalize(value: str) -> str:
    """Normalize a name/code for lookup: lowercase, strip non-alphanumerics."""
    name = (value or "").strip().lower()
    return "".join(ch for ch in name if ch.isalnum())


def _entry(code, display, aliases, unit=""):
    return {"code": code, "display": display, "unit": unit, "aliases": aliases}


# Canonical observables: local names used across the demo facilities are given
# as aliases so they all resolve to the same LOINC -> the same FHIR Observation.
OBSERVABLES = [
    _entry("1558-6", "Glucose [Mass/volume] in Serum or Plasma", unit="mg/dL",
           aliases=["glucose", "blood glucose", "blood sugar", "fasting blood sugar",
                    "fasting blood glucose", "fasting glucose", "fbs", "fbs sugar"]),
    _entry("2339-0", "Glucose [Mass/volume] in Capillary blood", unit="mg/dL",
           aliases=["random blood sugar", "random glucose", "rbs", "casual blood sugar"]),
    _entry("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", unit="%",
           aliases=["hba1c", "hb a1c", "glycated hemoglobin", "glycohemoglobin", "a1c"]),
    _entry("8462-4", "Systolic blood pressure", unit="mmHg",
           aliases=["blood pressure systolic", "systolic blood pressure", "systolic bp", "sbp"]),
    _entry("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", unit="mg/dL",
           aliases=["creatinine", "serum creatinine", "plasma creatinine"]),
    _entry("3094-0", "Urea [Mass/volume] in Serum or Plasma", unit="mg/dL",
           aliases=["urea", "blood urea", "blood urea nitrogen", "bun"]),
    _entry("718-7", "Hemoglobin [Mass/volume] in Blood", unit="g/dL",
           aliases=["hemoglobin", "haemoglobin", "hb", "blood hemoglobin"]),
    _entry("6690-2", "Leukocytes [#/volume] in Blood", unit="10^3/uL",
           aliases=["wbc", "white blood cell", "white blood cell count", "leukocyte",
                    "leukocyte count"]),
    _entry("777-3", "Platelets [#/volume] in Blood", unit="10^3/uL",
           aliases=["platelets", "platelet count", "plt"]),
    _entry("789-8", "Erythrocytes [#/volume] in Blood", unit="10^6/uL",
           aliases=["rbc", "red blood cell", "red blood cell count", "erythrocyte count"]),
    _entry("4544-3", "Hematocrit [Volume Fraction] of Blood", unit="%",
           aliases=["hematocrit", "packed cell volume", "pcv"]),
    _entry("4537-7", "Erythrocyte sedimentation rate", unit="mm/hr",
           aliases=["esr", "erythrocyte sedimentation rate"]),
    _entry("2089-1", "Cholesterol in LDL [Mass/volume] in Serum or Plasma", unit="mg/dL",
           aliases=["ldl", "ldl cholesterol", "cholesterol in ldl"]),
    _entry("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", unit="mg/dL",
           aliases=["total cholesterol", "cholesterol", "serum cholesterol"]),
    _entry("2571-8", "Triglyceride [Mass/volume] in Serum or Plasma", unit="mg/dL",
           aliases=["triglycerides", "triglyceride"]),
    _entry("2085-9", "Cholesterol in HDL [Mass/volume] in Serum or Plasma", unit="mg/dL",
           aliases=["hdl", "hdl cholesterol", "cholesterol in hdl"]),
    _entry("10839-9", "Troponin I.cardiac [Mass/volume] in Serum or Plasma", unit="ng/mL",
           aliases=["troponin i", "troponin", "ctnni"]),
    _entry("13969-1", "Creatine kinase.MB [Mass/volume] in Serum or Plasma", unit="ng/mL",
           aliases=["ck mb", "ckmb", "creatine kinase mb", "ck-mb"]),
    _entry("2951-2", "Sodium [Moles/volume] in Serum or Plasma", unit="mmol/L",
           aliases=["sodium", "na", "na+"])
]
# extended biochemical entries: potassium, bilirubin, transaminases, TSH, iron
OBSERVABLES += [
    _entry("2823-3", "Potassium [Moles/volume] in Serum or Plasma", unit="mmol/L",
           aliases=["potassium", "k", "k+"]),
    _entry("1975-2", "Bilirubin.total [Mass/volume] in Serum or Plasma", unit="mg/dL",
           aliases=["total bilirubin", "bilirubin total", "t bilirubin"]),
    _entry("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", unit="U/L",
           aliases=["alt", "sgpt", "alanine aminotransferase"]),
    _entry("1920-8", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", unit="U/L",
           aliases=["ast", "sgot", "aspartate aminotransferase"]),
    _entry("6768-6", "Alkaline phosphatase [Enzymatic activity/volume] in Serum or Plasma", unit="U/L",
           aliases=["alkaline phosphatase", "alp"]),
    _entry("1798-8", "Amylase [Enzymatic activity/volume] in Serum or Plasma", unit="U/L",
           aliases=["amylase", "serum amylase"]),
    _entry("3016-3", "Thyrotropin [Units/volume] in Serum or Plasma", unit="uIU/mL",
           aliases=["tsh", "thyroid stimulating hormone"]),
    _entry("3024-7", "Thyroxine (T4) free [Mass/volume] in Serum or Plasma", unit="ng/dL",
           aliases=["free t4", "t4 free"]),
    _entry("2498-4", "Iron [Mass/volume] in Serum or Plasma", unit="ug/dL",
           aliases=["iron", "serum iron"]),
    _entry("2276-4", "Ferritin [Mass/volume] in Serum or Plasma", unit="ng/mL",
           aliases=["ferritin"]),
    _entry("2132-9", "Cobalamin (Vitamin B12) [Mass/volume] in Serum or Plasma", unit="pg/mL",
           aliases=["vitamin b12", "b12", "cobalamin"]),
    _entry("5902-2", "Prothrombin time", unit="sec",
           aliases=["pt", "prothrombin time"]),
    _entry("6301-6", "International normalized ratio", unit="ratio",
           aliases=["inr", "international normalized ratio"]),
    _entry("3173-2", "Activated partial thromboplastin time", unit="sec",
           aliases=["aptt", "activated partial thromboplastin time"]),
]

# Canonical report panels (DiagnosticReport.code)
PANELS = [
    _entry("58410-2", "Complete blood count (hemogram) panel",
           aliases=["complete blood count", "cbc", "fbc", "full blood count", "hemogram"]),
    _entry("57698-3", "Lipid panel",
           aliases=["lipid profile", "lipid panel", "lipids"]),
    _entry("24323-0", "Basic metabolic panel",
           aliases=["basic metabolic panel", "bmp", "renal function test", "rft",
                    "renal profile", "renal panel"]),
]


def _build_index(entries):
    index = {}
    for entry in entries:
        code_key = normalize(entry["code"])
        index[code_key] = entry
        for alias in entry["aliases"]:
            alias_key = normalize(alias)
            if not alias_key:
                continue
            existing = index.get(alias_key)
            if existing is not None and existing["code"] != entry["code"]:
                raise ValueError(
                    f"Alias '{alias}' maps to both {existing['code']} and {entry['code']}"
                )
            index[alias_key] = entry
    return index


_OBSERVABLE_INDEX = _build_index(OBSERVABLES)
_PANEL_INDEX = _build_index(PANELS)


def _resolve(index, name_or_code):
    key = normalize(name_or_code)
    if not key:
        return None
    entry = index.get(key)
    if entry is None and LOINC_CODE_RE.match((name_or_code or "").strip()):
        entry = index.get(normalize(name_or_code)) or next(
            (e for e in index.values() if e["code"] == name_or_code.strip()), None
        )
    return entry


def observable_coding(name_or_code):
    """Canonical FHIR Coding for an observation (or None if unmapped)."""
    entry = _resolve(_OBSERVABLE_INDEX, name_or_code)
    if entry is None:
        return None
    return {"system": LOINC, "code": entry["code"], "display": entry["display"]}


def panel_coding(name_or_code):
    """Canonical FHIR Coding for a report panel (or None if unmapped)."""
    entry = _resolve(_PANEL_INDEX, name_or_code)
    if entry is None:
        return None
    return {"system": LOINC, "code": entry["code"], "display": entry["display"]}


def check_integrity():
    """
    Verify the terminology tables are conflict-free.

    Returns a list of human-readable issues (empty == healthy).
    Checks:
      - canonical codes look like LOINC (NNNNN-N)
      - no alias resolves to two different codes
      - no two entries share a canonical code
    """
    issues = []

    def scan(entries, kind):
        codes = {}
        for entry in entries:
            if not LOINC_CODE_RE.match(entry["code"]):
                issues.append(f"{kind} '{entry['display']}': code '{entry['code']}' is not LOINC-shaped")
            if entry["code"] in codes:
                issues.append(f"{kind} codes collide: {entry['code']} ({codes[entry['code']]} vs {entry['display']})")
            codes[entry["code"]] = entry["display"]

    scan(OBSERVABLES, "observable")
    scan(PANELS, "panel")

    # Alias collisions across the whole namespace (observable vs panel).
    seen = {}
    for entry in OBSERVABLES + PANELS:
        for alias in entry["aliases"]:
            key = normalize(alias)
            if key in seen and seen[key] != entry["code"]:
                issues.append(
                    f"alias '{alias}' maps to both {seen[key]} and {entry['code']}"
                )
            seen[key] = entry["code"]
    return issues
