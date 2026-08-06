"""
Laboratory test catalog — the single source of truth for this lab's test menu.

For every analyte we store:
  - loinc:  the LOINC code + display (for FHIR Observation.code.coding)
  - unit:   UCUM unit string (for FHIR valueQuantity.unit / .code)
  - low/high: numeric reference-range bounds (for FHIR referenceRange)
  - qualitative: True for report-type tests (serology/microbiology) that carry a
    text result string instead of a numeric valueQuantity.

Panels group analytes into orderable reports (FHIR DiagnosticReport). Both this
lab (Central Diagnostic, variant A) and Pathlabs Nepal (variant B) share an
identical catalog so the two independent services emit standardized, comparable
FHIR regardless of their different underlying column names / databases.

LOINC codes are the common, widely-used codes for each analyte. Reference ranges
are typical adult ranges and are illustrative for the demo.
"""

# analyte name -> metadata
ANALYTES = {
    # ---- Hematology ----
    "Hemoglobin":            {"loinc": ("718-7", "Hemoglobin [Mass/volume] in Blood"), "unit": "g/dL", "low": 12.0, "high": 17.0},
    "Total RBC Count":       {"loinc": ("789-8", "Erythrocytes [#/volume] in Blood"), "unit": "10*6/uL", "low": 4.2, "high": 5.9},
    "Total WBC Count":       {"loinc": ("6690-2", "Leukocytes [#/volume] in Blood"), "unit": "10*3/uL", "low": 4.0, "high": 11.0},
    "Platelet Count":        {"loinc": ("777-3", "Platelets [#/volume] in Blood"), "unit": "10*3/uL", "low": 150.0, "high": 450.0},
    "Hematocrit":            {"loinc": ("4544-3", "Hematocrit [Volume Fraction] of Blood"), "unit": "%", "low": 36.0, "high": 50.0},
    "MCV":                   {"loinc": ("787-2", "MCV [Entitic volume]"), "unit": "fL", "low": 80.0, "high": 100.0},
    "MCH":                   {"loinc": ("785-6", "MCH [Entitic mass]"), "unit": "pg", "low": 27.0, "high": 33.0},
    "MCHC":                  {"loinc": ("786-4", "MCHC [Mass/volume]"), "unit": "g/dL", "low": 32.0, "high": 36.0},
    "ESR":                   {"loinc": ("30341-2", "Erythrocyte sedimentation rate"), "unit": "mm/h", "low": 0.0, "high": 20.0},
    "Prothrombin Time":      {"loinc": ("5902-2", "Prothrombin time (PT)"), "unit": "s", "low": 11.0, "high": 13.5},
    "INR":                   {"loinc": ("6301-6", "INR in Platelet poor plasma"), "unit": "{ratio}", "low": 0.8, "high": 1.2},
    "aPTT":                  {"loinc": ("14979-9", "aPTT in Platelet poor plasma"), "unit": "s", "low": 25.0, "high": 35.0},

    # ---- Glucose / Diabetes ----
    "Fasting Blood Sugar":   {"loinc": ("1558-6", "Fasting glucose [Mass/volume] in Serum/Plasma"), "unit": "mg/dL", "low": 70.0, "high": 100.0},
    "Postprandial Blood Sugar": {"loinc": ("1521-4", "2 hour postprandial glucose"), "unit": "mg/dL", "low": 70.0, "high": 140.0},
    "Random Blood Sugar":    {"loinc": ("2345-7", "Glucose [Mass/volume] in Serum/Plasma"), "unit": "mg/dL", "low": 70.0, "high": 140.0},
    "HbA1c":                 {"loinc": ("4548-4", "Hemoglobin A1c/Hemoglobin.total"), "unit": "%", "low": 4.0, "high": 5.6},

    # ---- Lipid Profile ----
    "Total Cholesterol":     {"loinc": ("2093-3", "Cholesterol [Mass/volume] in Serum/Plasma"), "unit": "mg/dL", "low": 0.0, "high": 200.0},
    "LDL Cholesterol":       {"loinc": ("13457-7", "LDL cholesterol (calc)"), "unit": "mg/dL", "low": 0.0, "high": 100.0},
    "HDL Cholesterol":       {"loinc": ("2085-9", "HDL cholesterol [Mass/volume]"), "unit": "mg/dL", "low": 40.0, "high": 60.0},
    "Triglycerides":         {"loinc": ("2571-8", "Triglyceride [Mass/volume]"), "unit": "mg/dL", "low": 0.0, "high": 150.0},

    # ---- Liver Function (LFT) ----
    "Total Bilirubin":       {"loinc": ("1975-2", "Bilirubin.total [Mass/volume]"), "unit": "mg/dL", "low": 0.1, "high": 1.2},
    "Direct Bilirubin":      {"loinc": ("1968-7", "Bilirubin.direct [Mass/volume]"), "unit": "mg/dL", "low": 0.0, "high": 0.3},
    "SGPT / ALT":            {"loinc": ("1742-6", "Alanine aminotransferase [ALT]"), "unit": "U/L", "low": 7.0, "high": 56.0},
    "SGOT / AST":            {"loinc": ("1920-8", "Aspartate aminotransferase [AST]"), "unit": "U/L", "low": 5.0, "high": 40.0},
    "Alkaline Phosphatase":  {"loinc": ("6768-6", "Alkaline phosphatase [Enzymatic activity/volume]"), "unit": "U/L", "low": 44.0, "high": 147.0},
    "Total Protein":         {"loinc": ("2885-2", "Protein [Mass/volume] in Serum/Plasma"), "unit": "g/dL", "low": 6.4, "high": 8.3},
    "Albumin":               {"loinc": ("1751-7", "Albumin [Mass/volume] in Serum/Plasma"), "unit": "g/dL", "low": 3.5, "high": 5.2},

    # ---- Renal Function (RFT/KFT) ----
    "Urea":                  {"loinc": ("22664-7", "Urea [Mass/volume] in Serum/Plasma"), "unit": "mg/dL", "low": 15.0, "high": 40.0},
    "Blood Urea Nitrogen":   {"loinc": ("3094-0", "Urea nitrogen [Mass/volume] in Serum/Plasma"), "unit": "mg/dL", "low": 7.0, "high": 20.0},
    "Creatinine":            {"loinc": ("2160-0", "Creatinine [Mass/volume] in Serum/Plasma"), "unit": "mg/dL", "low": 0.6, "high": 1.2},
    "Uric Acid":             {"loinc": ("3084-1", "Urate [Mass/volume] in Serum/Plasma"), "unit": "mg/dL", "low": 3.5, "high": 7.2},

    # ---- Electrolytes ----
    "Sodium":                {"loinc": ("2951-2", "Sodium [Moles/volume] in Serum/Plasma"), "unit": "mmol/L", "low": 135.0, "high": 145.0},
    "Potassium":             {"loinc": ("2823-3", "Potassium [Moles/volume] in Serum/Plasma"), "unit": "mmol/L", "low": 3.5, "high": 5.1},
    "Chloride":              {"loinc": ("2075-0", "Chloride [Moles/volume] in Serum/Plasma"), "unit": "mmol/L", "low": 98.0, "high": 107.0},
    "Calcium":               {"loinc": ("17861-6", "Calcium [Mass/volume] in Serum/Plasma"), "unit": "mg/dL", "low": 8.6, "high": 10.2},

    # ---- Thyroid ----
    "TSH":                   {"loinc": ("3016-3", "Thyrotropin [Units/volume]"), "unit": "mIU/L", "low": 0.4, "high": 4.0},
    "Free T3":               {"loinc": ("3051-0", "Triiodothyronine (T3) Free"), "unit": "pg/mL", "low": 2.3, "high": 4.2},
    "Free T4":               {"loinc": ("3024-7", "Thyroxine (T4) free [Mass/volume]"), "unit": "ng/dL", "low": 0.8, "high": 1.8},

    # ---- Vitamins ----
    "Vitamin D (25-OH)":     {"loinc": ("1989-3", "25-hydroxyvitamin D3 [Mass/volume]"), "unit": "ng/mL", "low": 30.0, "high": 100.0},
    "Vitamin B12":           {"loinc": ("2132-9", "Cobalamin (Vitamin B12) [Mass/volume]"), "unit": "pg/mL", "low": 200.0, "high": 900.0},

    # ---- Cardiac Markers ----
    "Troponin I":            {"loinc": ("10839-9", "Troponin I.cardiac [Mass/volume]"), "unit": "ng/mL", "low": 0.0, "high": 0.04},
    "CK-MB":                 {"loinc": ("13969-1", "Creatine kinase.MB [Mass/volume]"), "unit": "ng/mL", "low": 0.0, "high": 5.0},
    "D-Dimer":               {"loinc": ("48065-7", "D-dimer FEU [Mass/volume]"), "unit": "ng/mL FEU", "low": 0.0, "high": 500.0},

    # ---- Iron Studies ----
    "Serum Iron":            {"loinc": ("2498-4", "Iron [Mass/volume] in Serum/Plasma"), "unit": "ug/dL", "low": 60.0, "high": 170.0},
    "Ferritin":              {"loinc": ("2276-4", "Ferritin [Mass/volume] in Serum/Plasma"), "unit": "ng/mL", "low": 30.0, "high": 400.0},
    "TIBC":                  {"loinc": ("2500-7", "Iron binding capacity [Mass/volume]"), "unit": "ug/dL", "low": 240.0, "high": 450.0},

    # ---- Inflammatory / Serology (quantitative) ----
    "C-Reactive Protein":    {"loinc": ("1988-5", "C reactive protein [Mass/volume]"), "unit": "mg/L", "low": 0.0, "high": 5.0},

    # ---- Serology / Infectious (qualitative report-type) ----
    "HBsAg":                 {"loinc": ("5195-3", "Hepatitis B virus surface Ag"), "qualitative": True},
    "Anti-HCV":              {"loinc": ("16128-1", "Hepatitis C virus Ab"), "qualitative": True},
    "HIV I/II":              {"loinc": ("75622-1", "HIV 1 and 2 Ab+Ag"), "qualitative": True},
    "VDRL":                  {"loinc": ("5292-8", "Reagin Ab [Presence] (VDRL)"), "qualitative": True},
    "Widal Test":            {"loinc": ("6491-5", "Salmonella sp Ab [Titer] (Widal)"), "qualitative": True},
    "Typhidot IgM":          {"loinc": ("40679-2", "Salmonella typhi IgM"), "qualitative": True},
    "Dengue NS1 Antigen":    {"loinc": ("75695-7", "Dengue virus NS1 Ag"), "qualitative": True},
    "Dengue IgM":            {"loinc": ("25340-6", "Dengue virus IgM"), "qualitative": True},
    "Malaria Antigen":       {"loinc": ("70168-0", "Plasmodium sp Ag"), "qualitative": True},
    "Scrub Typhus IgM":      {"loinc": ("53818-1", "Orientia tsutsugamushi IgM"), "qualitative": True},

    # ---- Urine / Microbiology (qualitative report-type) ----
    "Urine Routine & Microscopy": {"loinc": ("24357-6", "Urinalysis complete panel"), "qualitative": True},
    "Stool Routine & Microscopy": {"loinc": ("10366-3", "Stool microscopic exam"), "qualitative": True},
    "Culture & Sensitivity": {"loinc": ("618-9", "Bacteria identified in culture"), "qualitative": True},
}

# Panel name -> LOINC (panel-level) + ordered analyte list.
PANELS = {
    "Complete Blood Count": {
        "loinc": ("58410-2", "CBC panel - Blood by Automated count"),
        "analytes": ["Hemoglobin", "Total RBC Count", "Total WBC Count", "Platelet Count",
                     "Hematocrit", "MCV", "MCH", "MCHC"],
    },
    "Coagulation Profile": {
        "loinc": ("34534-8", "Coagulation panel"),
        "analytes": ["Prothrombin Time", "INR", "aPTT"],
    },
    "Lipid Profile": {
        "loinc": ("57698-3", "Lipid panel with direct LDL"),
        "analytes": ["Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides"],
    },
    "Liver Function Test": {
        "loinc": ("24325-3", "Hepatic function panel"),
        "analytes": ["Total Bilirubin", "Direct Bilirubin", "SGPT / ALT", "SGOT / AST",
                     "Alkaline Phosphatase", "Total Protein", "Albumin"],
    },
    "Renal Function Test": {
        "loinc": ("24362-6", "Renal function panel"),
        "analytes": ["Urea", "Blood Urea Nitrogen", "Creatinine", "Uric Acid"],
    },
    "Electrolyte Panel": {
        "loinc": ("55231-5", "Electrolytes panel"),
        "analytes": ["Sodium", "Potassium", "Chloride", "Calcium"],
    },
    "Diabetic Profile": {
        "loinc": ("55399-0", "Diabetes tracking panel"),
        "analytes": ["Fasting Blood Sugar", "Postprandial Blood Sugar", "HbA1c"],
    },
    "Thyroid Function Test": {
        "loinc": ("55204-3", "Thyroid function panel"),
        "analytes": ["TSH", "Free T3", "Free T4"],
    },
    "Cardiac Markers": {
        "loinc": ("34530-6", "Cardiac markers panel"),
        "analytes": ["Troponin I", "CK-MB", "D-Dimer"],
    },
    "Iron Studies": {
        "loinc": ("24363-4", "Iron studies panel"),
        "analytes": ["Serum Iron", "Ferritin", "TIBC"],
    },
    "Vitamin Assay": {
        "loinc": ("100073-2", "Vitamin panel"),
        "analytes": ["Vitamin D (25-OH)", "Vitamin B12"],
    },
    "Viral Markers": {
        "loinc": ("34578-5", "Viral markers panel"),
        "analytes": ["HBsAg", "Anti-HCV", "HIV I/II", "VDRL"],
    },
    "Febrile Illness Panel": {
        "loinc": ("100544-2", "Acute febrile illness panel"),
        "analytes": ["Widal Test", "Typhidot IgM", "Dengue NS1 Antigen", "Dengue IgM",
                     "Malaria Antigen", "Scrub Typhus IgM", "C-Reactive Protein"],
    },
    "Urine Routine Examination": {
        "loinc": ("24356-8", "Urinalysis panel"),
        "analytes": ["Urine Routine & Microscopy"],
    },
    "Stool Examination": {
        "loinc": ("10366-3", "Stool microscopic exam"),
        "analytes": ["Stool Routine & Microscopy", "Culture & Sensitivity"],
    },
}


def analyte_meta(name):
    """Return metadata dict for an analyte, or a safe empty default."""
    return ANALYTES.get(name, {})


def panel_meta(name):
    return PANELS.get(name, {})


def is_qualitative(name):
    return bool(ANALYTES.get(name, {}).get("qualitative"))
