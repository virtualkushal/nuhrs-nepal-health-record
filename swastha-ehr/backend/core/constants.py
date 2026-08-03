"""
Shared constants for the SwasthyaEHR domain (v2 — multi-department OPD).

Single source of truth for models, serializers, and validators. Mirrors
docs/DATABASE_SCHEMA.md — if they ever disagree, the schema doc wins.

v2 scope: a multi-department hospital OPD EHR covering 7 clinical departments,
7 laboratory categories, ICD-10 coded diagnoses, and a unified lab test catalog
with two result types (quantitative and report/qualitative).
"""


class Role:
    """Staff/user roles. Stored as UPPER_SNAKE_CASE strings on the user model."""

    ADMIN = "ADMIN"
    RECEPTIONIST = "RECEPTIONIST"
    NURSE = "NURSE"
    DOCTOR = "DOCTOR"
    LAB_TECH = "LAB_TECH"
    PHARMACIST = "PHARMACIST"
    PATIENT = "PATIENT"

    CHOICES = [
        (ADMIN, "System Administrator"),
        (RECEPTIONIST, "Receptionist"),
        (NURSE, "Nurse"),
        (DOCTOR, "Doctor"),
        (LAB_TECH, "Laboratory Technician"),
        (PHARMACIST, "Pharmacist"),
        (PATIENT, "Patient"),
    ]

    # Clinical staff roles that self-register and need admin approval.
    STAFF_ROLES = [RECEPTIONIST, NURSE, DOCTOR, LAB_TECH, PHARMACIST]


class StaffStatus:
    """Onboarding lifecycle for a self-registered staff account."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"

    CHOICES = [
        (PENDING, "Pending approval"),
        (ACTIVE, "Active"),
        (REJECTED, "Rejected"),
    ]


class Gender:
    """Lowercase to satisfy the FHIR `Patient.gender` requirement."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"

    CHOICES = [
        (MALE, "Male"),
        (FEMALE, "Female"),
        (OTHER, "Other"),
        (UNKNOWN, "Unknown"),
    ]


class BloodGroup:
    """The 8 standard ABO/Rh blood groups (patient-declared at registration)."""

    CHOICES = [
        ("A+", "A positive"),
        ("A-", "A negative"),
        ("B+", "B positive"),
        ("B-", "B negative"),
        ("AB+", "AB positive"),
        ("AB-", "AB negative"),
        ("O+", "O positive"),
        ("O-", "O negative"),
        ("UNKNOWN", "Unknown"),
    ]

    VALUES = [c[0] for c in CHOICES]


class MaritalStatus:
    CHOICES = [
        ("SINGLE", "Single"),
        ("MARRIED", "Married"),
        ("DIVORCED", "Divorced"),
        ("WIDOWED", "Widowed"),
        ("OTHER", "Other"),
    ]


class RegisteredBy:
    """How a patient profile row was created."""

    SELF = "SELF"
    RECEPTIONIST = "RECEPTIONIST"

    CHOICES = [
        (SELF, "Self (public form)"),
        (RECEPTIONIST, "Receptionist"),
    ]


class Department:
    """
    The 7 clinical departments (services) the hospital runs. A department is a
    tag on each encounter and on each staff member (doctors belong to one).
    """

    ENDOCRINOLOGY = "ENDOCRINOLOGY"
    INTERNAL_MEDICINE = "INTERNAL_MEDICINE"
    NEPHROLOGY = "NEPHROLOGY"
    CARDIOLOGY = "CARDIOLOGY"
    GASTROENTEROLOGY = "GASTROENTEROLOGY"
    INFECTIOUS_DISEASES = "INFECTIOUS_DISEASES"
    HEMATOLOGY = "HEMATOLOGY"

    CHOICES = [
        (ENDOCRINOLOGY, "Diabetes & Endocrinology"),
        (INTERNAL_MEDICINE, "Internal Medicine"),
        (NEPHROLOGY, "Nephrology"),
        (CARDIOLOGY, "Cardiology"),
        (GASTROENTEROLOGY, "Gastroenterology / Hepatobiliary"),
        (INFECTIOUS_DISEASES, "Infectious Diseases"),
        (HEMATOLOGY, "Hematology"),
    ]

    VALUES = [c[0] for c in CHOICES]


class LabCategory:
    """The 7 laboratory categories (diagnostic services)."""

    BIOCHEMISTRY = "BIOCHEMISTRY"
    HEMATOLOGY = "HEMATOLOGY"
    URINALYSIS = "URINALYSIS"
    MICROBIOLOGY = "MICROBIOLOGY"
    SEROLOGY = "SEROLOGY"
    COAGULATION = "COAGULATION"
    BLOOD_BANK = "BLOOD_BANK"

    CHOICES = [
        (BIOCHEMISTRY, "Biochemistry"),
        (HEMATOLOGY, "Hematology"),
        (URINALYSIS, "Urinalysis"),
        (MICROBIOLOGY, "Microbiology"),
        (SEROLOGY, "Serology / Immunology"),
        (COAGULATION, "Coagulation"),
        (BLOOD_BANK, "Blood Bank"),
    ]


class LabResultType:
    """
    Two kinds of lab results:
    - QUANTITATIVE: a numeric value + unit + reference range + HIGH/LOW/NORMAL
    - REPORT: a qualitative / narrative result (e.g. culture, blood grouping)
    """

    QUANTITATIVE = "QUANTITATIVE"
    REPORT = "REPORT"

    CHOICES = [
        (QUANTITATIVE, "Quantitative (numeric)"),
        (REPORT, "Report / Qualitative"),
    ]


class ResultFlag:
    """Auto-computed flag for a quantitative result vs its reference range."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"

    CHOICES = [(LOW, "Low"), (NORMAL, "Normal"), (HIGH, "High")]


class LabResultSource:
    """
    How a lab result's values were captured. `MANUAL` for typed entry now;
    `PDF_EXTRACTED` reserved for the future PDF-upload pipeline so it slots in
    with no schema rework.
    """

    MANUAL = "MANUAL"
    PDF_EXTRACTED = "PDF_EXTRACTED"

    CHOICES = [
        (MANUAL, "Manual entry"),
        (PDF_EXTRACTED, "Extracted from PDF"),
    ]


class LabOrderStatus:
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"

    CHOICES = [(PENDING, "Pending"), (COMPLETED, "Completed")]


class LabOrderPriority:
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"

    CHOICES = [(ROUTINE, "Routine"), (URGENT, "Urgent")]


class PrescriptionStatus:
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

    CHOICES = [(ACTIVE, "Active"), (COMPLETED, "Completed")]


class DiagnosisStatus:
    """Clinical status of a recorded diagnosis (FHIR Condition.clinicalStatus)."""

    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"

    CHOICES = [(ACTIVE, "Active"), (RESOLVED, "Resolved")]


class EncounterStatus:
    """
    Status-driven OPD queue. Each role sees encounters relevant to their step.
    REGISTERED -> VITALS_DONE -> WITH_DOCTOR -> LAB_PENDING -> LAB_DONE -> CLOSED
    """

    REGISTERED = "REGISTERED"
    VITALS_DONE = "VITALS_DONE"
    WITH_DOCTOR = "WITH_DOCTOR"
    LAB_PENDING = "LAB_PENDING"
    LAB_DONE = "LAB_DONE"
    CLOSED = "CLOSED"

    CHOICES = [
        (REGISTERED, "Registered"),
        (VITALS_DONE, "Vitals recorded"),
        (WITH_DOCTOR, "With doctor"),
        (LAB_PENDING, "Awaiting lab"),
        (LAB_DONE, "Lab complete"),
        (CLOSED, "Closed"),
    ]


class VisitType:
    NEW = "NEW"
    FOLLOWUP = "FOLLOWUP"

    CHOICES = [(NEW, "New visit"), (FOLLOWUP, "Follow-up")]


class AccessRequestStatus:
    """Cross-hospital FHIR record-share request lifecycle (patient approves)."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"

    CHOICES = [
        (PENDING, "Pending patient approval"),
        (APPROVED, "Approved"),
        (DENIED, "Denied"),
        (EXPIRED, "Expired"),
    ]


class LabTestCatalog:
    """
    The unified master lab test catalog. Every orderable test lives here, tagged
    with its lab category, the department(s) that commonly order it, its result
    type, and (for quantitative tests) LOINC code + unit + adult reference range.

    Reference ranges are simple adult ranges (one range per test). Age/sex-
    specific ranges are future work. Ranges should be spot-checked against a
    real Nepali lab report before final defense.

    Each entry key is the canonical test code (UPPER_SNAKE_CASE). Fields:
      name        human-readable name
      category    LabCategory value
      type        LabResultType value
      loinc       LOINC code (quantitative) or "" for report-type
      unit        unit string (quantitative) or ""
      low, high   adult reference range (quantitative) or None
      depts       list of Department values that commonly order it
    """

    TESTS = {
        # --- Biochemistry (quantitative) ---
        "HBA1C": {"name": "HbA1c (Glycated Hemoglobin)", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "4548-4", "unit": "%", "low": 4.0, "high": 5.6, "depts": [Department.ENDOCRINOLOGY, Department.INTERNAL_MEDICINE]},
        "FBS": {"name": "Fasting Blood Sugar", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "1558-6", "unit": "mg/dL", "low": 70.0, "high": 100.0, "depts": [Department.ENDOCRINOLOGY, Department.INTERNAL_MEDICINE]},
        "RBS": {"name": "Random Blood Sugar", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2339-0", "unit": "mg/dL", "low": 70.0, "high": 140.0, "depts": [Department.ENDOCRINOLOGY, Department.INTERNAL_MEDICINE]},
        "UREA": {"name": "Blood Urea", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "3094-0", "unit": "mg/dL", "low": 15.0, "high": 40.0, "depts": [Department.NEPHROLOGY, Department.INTERNAL_MEDICINE]},
        "CREATININE": {"name": "Serum Creatinine", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2160-0", "unit": "mg/dL", "low": 0.6, "high": 1.3, "depts": [Department.NEPHROLOGY, Department.ENDOCRINOLOGY, Department.INTERNAL_MEDICINE]},
        "SODIUM": {"name": "Sodium (Na+)", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2951-2", "unit": "mmol/L", "low": 135.0, "high": 145.0, "depts": [Department.NEPHROLOGY]},
        "POTASSIUM": {"name": "Potassium (K+)", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2823-3", "unit": "mmol/L", "low": 3.5, "high": 5.1, "depts": [Department.NEPHROLOGY]},
        "TOTAL_CHOLESTEROL": {"name": "Total Cholesterol", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2093-3", "unit": "mg/dL", "low": 0.0, "high": 200.0, "depts": [Department.CARDIOLOGY, Department.ENDOCRINOLOGY]},
        "TRIGLYCERIDES": {"name": "Triglycerides", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2571-8", "unit": "mg/dL", "low": 0.0, "high": 150.0, "depts": [Department.CARDIOLOGY, Department.ENDOCRINOLOGY]},
        "HDL": {"name": "HDL Cholesterol", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2085-9", "unit": "mg/dL", "low": 40.0, "high": 100.0, "depts": [Department.CARDIOLOGY, Department.ENDOCRINOLOGY]},
        "LDL": {"name": "LDL Cholesterol", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2089-1", "unit": "mg/dL", "low": 0.0, "high": 100.0, "depts": [Department.CARDIOLOGY, Department.ENDOCRINOLOGY]},
        "BILIRUBIN_TOTAL": {"name": "Total Bilirubin", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "1975-2", "unit": "mg/dL", "low": 0.3, "high": 1.2, "depts": [Department.GASTROENTEROLOGY]},
        "ALT": {"name": "ALT (SGPT)", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "1742-6", "unit": "U/L", "low": 7.0, "high": 56.0, "depts": [Department.GASTROENTEROLOGY]},
        "AST": {"name": "AST (SGOT)", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "1920-8", "unit": "U/L", "low": 10.0, "high": 40.0, "depts": [Department.GASTROENTEROLOGY]},
        "ALP": {"name": "Alkaline Phosphatase", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "6768-6", "unit": "U/L", "low": 44.0, "high": 147.0, "depts": [Department.GASTROENTEROLOGY]},
        "AMYLASE": {"name": "Serum Amylase", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "1798-8", "unit": "U/L", "low": 25.0, "high": 125.0, "depts": [Department.GASTROENTEROLOGY]},
        "TROPONIN_I": {"name": "Troponin I", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "10839-9", "unit": "ng/mL", "low": 0.0, "high": 0.04, "depts": [Department.CARDIOLOGY]},
        "CK_MB": {"name": "CK-MB", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "13969-1", "unit": "ng/mL", "low": 0.0, "high": 5.0, "depts": [Department.CARDIOLOGY]},
        "CRP": {"name": "C-Reactive Protein (CRP)", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "1988-5", "unit": "mg/L", "low": 0.0, "high": 6.0, "depts": [Department.INFECTIOUS_DISEASES, Department.INTERNAL_MEDICINE]},
        "TSH": {"name": "TSH", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "3016-3", "unit": "uIU/mL", "low": 0.4, "high": 4.0, "depts": [Department.ENDOCRINOLOGY]},
        "FREE_T4": {"name": "Free T4", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "3024-7", "unit": "ng/dL", "low": 0.8, "high": 1.8, "depts": [Department.ENDOCRINOLOGY]},
        "IRON": {"name": "Serum Iron", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2498-4", "unit": "ug/dL", "low": 60.0, "high": 170.0, "depts": [Department.HEMATOLOGY]},
        "FERRITIN": {"name": "Ferritin", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2276-4", "unit": "ng/mL", "low": 12.0, "high": 300.0, "depts": [Department.HEMATOLOGY]},
        "VITAMIN_B12": {"name": "Vitamin B12", "category": LabCategory.BIOCHEMISTRY, "type": LabResultType.QUANTITATIVE, "loinc": "2132-9", "unit": "pg/mL", "low": 200.0, "high": 900.0, "depts": [Department.HEMATOLOGY]},
        # --- Hematology (quantitative) ---
        "HEMOGLOBIN": {"name": "Hemoglobin", "category": LabCategory.HEMATOLOGY, "type": LabResultType.QUANTITATIVE, "loinc": "718-7", "unit": "g/dL", "low": 12.0, "high": 17.0, "depts": [Department.HEMATOLOGY, Department.INTERNAL_MEDICINE, Department.NEPHROLOGY]},
        "WBC": {"name": "White Blood Cell Count", "category": LabCategory.HEMATOLOGY, "type": LabResultType.QUANTITATIVE, "loinc": "6690-2", "unit": "10^3/uL", "low": 4.0, "high": 11.0, "depts": [Department.HEMATOLOGY, Department.INFECTIOUS_DISEASES, Department.INTERNAL_MEDICINE]},
        "PLATELETS": {"name": "Platelet Count", "category": LabCategory.HEMATOLOGY, "type": LabResultType.QUANTITATIVE, "loinc": "777-3", "unit": "10^3/uL", "low": 150.0, "high": 450.0, "depts": [Department.HEMATOLOGY, Department.INFECTIOUS_DISEASES]},
        "RBC": {"name": "Red Blood Cell Count", "category": LabCategory.HEMATOLOGY, "type": LabResultType.QUANTITATIVE, "loinc": "789-8", "unit": "10^6/uL", "low": 4.2, "high": 5.9, "depts": [Department.HEMATOLOGY]},
        "HEMATOCRIT": {"name": "Hematocrit (PCV)", "category": LabCategory.HEMATOLOGY, "type": LabResultType.QUANTITATIVE, "loinc": "4544-3", "unit": "%", "low": 36.0, "high": 50.0, "depts": [Department.HEMATOLOGY]},
        "ESR": {"name": "ESR", "category": LabCategory.HEMATOLOGY, "type": LabResultType.QUANTITATIVE, "loinc": "4537-7", "unit": "mm/hr", "low": 0.0, "high": 20.0, "depts": [Department.INFECTIOUS_DISEASES, Department.INTERNAL_MEDICINE]},
        # --- Urinalysis ---
        "URINE_MICROALBUMIN": {"name": "Urine Microalbumin", "category": LabCategory.URINALYSIS, "type": LabResultType.QUANTITATIVE, "loinc": "14957-5", "unit": "mg/L", "low": 0.0, "high": 30.0, "depts": [Department.NEPHROLOGY, Department.ENDOCRINOLOGY]},
        "URINE_ROUTINE": {"name": "Urine Routine & Microscopy", "category": LabCategory.URINALYSIS, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.NEPHROLOGY, Department.INTERNAL_MEDICINE]},
        # --- Coagulation (quantitative) ---
        "PT": {"name": "Prothrombin Time (PT)", "category": LabCategory.COAGULATION, "type": LabResultType.QUANTITATIVE, "loinc": "5902-2", "unit": "sec", "low": 11.0, "high": 13.5, "depts": [Department.CARDIOLOGY, Department.HEMATOLOGY]},
        "INR": {"name": "INR", "category": LabCategory.COAGULATION, "type": LabResultType.QUANTITATIVE, "loinc": "6301-6", "unit": "ratio", "low": 0.8, "high": 1.2, "depts": [Department.CARDIOLOGY, Department.HEMATOLOGY]},
        "APTT": {"name": "APTT", "category": LabCategory.COAGULATION, "type": LabResultType.QUANTITATIVE, "loinc": "3173-2", "unit": "sec", "low": 25.0, "high": 35.0, "depts": [Department.CARDIOLOGY, Department.HEMATOLOGY]},
        # --- Serology / Immunology (report / qualitative) ---
        "DENGUE_NS1": {"name": "Dengue NS1 Antigen", "category": LabCategory.SEROLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.INFECTIOUS_DISEASES, Department.INTERNAL_MEDICINE]},
        "HBSAG": {"name": "HBsAg (Hepatitis B)", "category": LabCategory.SEROLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.GASTROENTEROLOGY, Department.INFECTIOUS_DISEASES]},
        "ANTI_HCV": {"name": "Anti-HCV (Hepatitis C)", "category": LabCategory.SEROLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.GASTROENTEROLOGY, Department.INFECTIOUS_DISEASES]},
        "HIV": {"name": "HIV Antibody", "category": LabCategory.SEROLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.INFECTIOUS_DISEASES]},
        "WIDAL": {"name": "Widal Test (Typhoid)", "category": LabCategory.SEROLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.INFECTIOUS_DISEASES, Department.INTERNAL_MEDICINE]},
        "MALARIA_ANTIGEN": {"name": "Malaria Antigen", "category": LabCategory.SEROLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.INFECTIOUS_DISEASES]},
        "ANTI_TPO": {"name": "Anti-TPO (Thyroid Antibody)", "category": LabCategory.SEROLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.ENDOCRINOLOGY]},
        # --- Microbiology (report) ---
        "BLOOD_CULTURE": {"name": "Blood Culture & Sensitivity", "category": LabCategory.MICROBIOLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.INFECTIOUS_DISEASES, Department.INTERNAL_MEDICINE]},
        "URINE_CULTURE": {"name": "Urine Culture & Sensitivity", "category": LabCategory.MICROBIOLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.NEPHROLOGY, Department.INFECTIOUS_DISEASES]},
        "STOOL_CULTURE": {"name": "Stool Culture", "category": LabCategory.MICROBIOLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.GASTROENTEROLOGY, Department.INFECTIOUS_DISEASES]},
        "SPUTUM_AFB": {"name": "Sputum AFB (TB)", "category": LabCategory.MICROBIOLOGY, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.INFECTIOUS_DISEASES]},
        # --- Blood Bank (report) ---
        "BLOOD_GROUP": {"name": "Blood Grouping (ABO/Rh)", "category": LabCategory.BLOOD_BANK, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.HEMATOLOGY, Department.NEPHROLOGY]},
        "CROSSMATCH": {"name": "Crossmatch / Compatibility", "category": LabCategory.BLOOD_BANK, "type": LabResultType.REPORT, "loinc": "", "unit": "", "low": None, "high": None, "depts": [Department.HEMATOLOGY, Department.NEPHROLOGY]},
    }

    CHOICES = [(code, meta["name"]) for code, meta in TESTS.items()]

    @classmethod
    def get(cls, code):
        return cls.TESTS.get(code)

    @classmethod
    def is_valid(cls, code):
        return code in cls.TESTS

    @classmethod
    def for_department(cls, dept):
        """Tests commonly ordered by a given department."""
        return {c: m for c, m in cls.TESTS.items() if dept in m["depts"]}


# --------------------------------------------------------------------------- #
# Backward-compat shims (until models are rewritten in the next branch).
# The legacy Staff/LabObservation models still import `LabTest` and
# `ALLERGEN_VOCABULARY`; keep them so the app stays importable.
# --------------------------------------------------------------------------- #


class LabTest:
    """DEPRECATED legacy 3-test enum. Superseded by LabTestCatalog."""

    HEMOGLOBIN = "HEMOGLOBIN"
    WBC = "WBC"
    PLATELETS = "PLATELETS"

    CHOICES = [
        (HEMOGLOBIN, "Hemoglobin"),
        (WBC, "White Blood Cells"),
        (PLATELETS, "Platelets"),
    ]

    REFERENCE = {
        HEMOGLOBIN: {"loinc": "718-7", "unit": "g/dL", "min": 0.00, "max": 25.00},
        WBC: {"loinc": "6690-2", "unit": "10^3/uL", "min": 0.00, "max": 50.00},
        PLATELETS: {"loinc": "777-3", "unit": "10^3/uL", "min": 0.00, "max": 1000.00},
    }


# DEPRECATED: free-text allergies are used in v2; this fixed list is retained
# only for legacy imports and will be removed with the model rewrite.
ALLERGEN_VOCABULARY = [
    "Penicillin",
    "Sulfa Drugs",
    "Aspirin",
    "NSAIDs",
    "Anticonvulsants",
    "None",
]


class ICD10:
    """
    Curated ICD-10 diagnosis vocabulary, grouped by the 7 departments. A doctor
    records a diagnosis by picking from this fixed, coded list so every stored
    condition carries a valid, interoperable ICD-10 code (WHO standard, used for
    national reporting in Nepal). The system only RECORDS a doctor's chosen
    diagnosis; it never auto-diagnoses.

    Each entry: code -> {"name": display, "dept": Department}.
    """

    ENTRIES = {
        # Diabetes & Endocrinology
        "E11.9": {"name": "Type 2 diabetes mellitus", "dept": Department.ENDOCRINOLOGY},
        "E10.9": {"name": "Type 1 diabetes mellitus", "dept": Department.ENDOCRINOLOGY},
        "O24.4": {"name": "Gestational diabetes mellitus", "dept": Department.ENDOCRINOLOGY},
        "R73.0": {"name": "Prediabetes / impaired fasting glucose", "dept": Department.ENDOCRINOLOGY},
        "E03.9": {"name": "Hypothyroidism, unspecified", "dept": Department.ENDOCRINOLOGY},
        "E05.9": {"name": "Hyperthyroidism, unspecified", "dept": Department.ENDOCRINOLOGY},
        "M81.0": {"name": "Osteoporosis", "dept": Department.ENDOCRINOLOGY},
        # Internal Medicine
        "I10": {"name": "Essential (primary) hypertension", "dept": Department.INTERNAL_MEDICINE},
        "J18.9": {"name": "Pneumonia, unspecified", "dept": Department.INTERNAL_MEDICINE},
        "J45.9": {"name": "Asthma", "dept": Department.INTERNAL_MEDICINE},
        "A90": {"name": "Dengue fever", "dept": Department.INTERNAL_MEDICINE},
        "A01.0": {"name": "Typhoid fever", "dept": Department.INTERNAL_MEDICINE},
        "R50.9": {"name": "Fever, unspecified", "dept": Department.INTERNAL_MEDICINE},
        # Nephrology
        "N18.9": {"name": "Chronic kidney disease, unspecified", "dept": Department.NEPHROLOGY},
        "N17.9": {"name": "Acute kidney injury", "dept": Department.NEPHROLOGY},
        "N20.0": {"name": "Kidney stone (calculus)", "dept": Department.NEPHROLOGY},
        "N04.9": {"name": "Nephrotic syndrome", "dept": Department.NEPHROLOGY},
        "N39.0": {"name": "Urinary tract infection", "dept": Department.NEPHROLOGY},
        # Cardiology
        "I21.9": {"name": "Acute myocardial infarction", "dept": Department.CARDIOLOGY},
        "I50.9": {"name": "Heart failure, unspecified", "dept": Department.CARDIOLOGY},
        "I25.1": {"name": "Atherosclerotic heart disease", "dept": Department.CARDIOLOGY},
        "I49.9": {"name": "Cardiac arrhythmia, unspecified", "dept": Department.CARDIOLOGY},
        "E78.5": {"name": "Hyperlipidaemia / dyslipidemia", "dept": Department.CARDIOLOGY},
        # Gastroenterology / Hepatobiliary
        "B16.9": {"name": "Acute hepatitis B", "dept": Department.GASTROENTEROLOGY},
        "B18.2": {"name": "Chronic hepatitis C", "dept": Department.GASTROENTEROLOGY},
        "K74.6": {"name": "Cirrhosis of liver", "dept": Department.GASTROENTEROLOGY},
        "K29.7": {"name": "Gastritis, unspecified", "dept": Department.GASTROENTEROLOGY},
        "K85.9": {"name": "Acute pancreatitis", "dept": Department.GASTROENTEROLOGY},
        "K80.2": {"name": "Gallstone (calculus of gallbladder)", "dept": Department.GASTROENTEROLOGY},
        "K76.0": {"name": "Fatty liver (non-alcoholic)", "dept": Department.GASTROENTEROLOGY},
        # Infectious Diseases
        "A15.9": {"name": "Respiratory tuberculosis", "dept": Department.INFECTIOUS_DISEASES},
        "U07.1": {"name": "COVID-19", "dept": Department.INFECTIOUS_DISEASES},
        "B54": {"name": "Malaria, unspecified", "dept": Department.INFECTIOUS_DISEASES},
        "B20": {"name": "HIV disease", "dept": Department.INFECTIOUS_DISEASES},
        "A41.9": {"name": "Sepsis, unspecified", "dept": Department.INFECTIOUS_DISEASES},
        # Hematology
        "D64.9": {"name": "Anaemia, unspecified", "dept": Department.HEMATOLOGY},
        "D50.9": {"name": "Iron deficiency anaemia", "dept": Department.HEMATOLOGY},
        "C95.9": {"name": "Leukaemia, unspecified", "dept": Department.HEMATOLOGY},
        "C85.9": {"name": "Non-Hodgkin lymphoma", "dept": Department.HEMATOLOGY},
        "D68.9": {"name": "Coagulation / bleeding disorder", "dept": Department.HEMATOLOGY},
    }

    # Legacy flat mapping (code -> name) retained for existing callers.
    CODES = {code: meta["name"] for code, meta in ENTRIES.items()}

    CHOICES = [(code, f"{code} — {meta['name']}") for code, meta in ENTRIES.items()]

    @classmethod
    def is_valid(cls, code):
        return code in cls.ENTRIES

    @classmethod
    def display(cls, code):
        entry = cls.ENTRIES.get(code)
        return entry["name"] if entry else ""

    @classmethod
    def department_of(cls, code):
        entry = cls.ENTRIES.get(code)
        return entry["dept"] if entry else None

    @classmethod
    def for_department(cls, dept):
        return {c: m for c, m in cls.ENTRIES.items() if m["dept"] == dept}


