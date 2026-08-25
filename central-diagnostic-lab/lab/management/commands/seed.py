"""
Seed Central Diagnostic Laboratory with comprehensive demo reports.

Uses the shared NIDs (2345678901, 02, 03) so reports merge into the unified
exchange. Demographics are CANONICAL per NID. Each panel gets multiple dated
reports (a series) for trend visualization.

All writers are IDEMPOTENT (get_or_create on natural keys) so re-running never
inserts duplicate rows at the same date.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from lab import catalog, services
from lab.models import LabPatient, LabReport, LabResult

ORG_CODE = settings.ORG_CODE

# Canonical demographics per NID — MUST match the hospital and swastha seeds.
DEMOGRAPHICS = {
    "2345678901": {"name": "Ram Bahadur Thapa", "dob": "1970-05-12", "gender": "MALE", "phone": "9841000001"},
    "2345678902": {"name": "Sita Kumari Sharma", "dob": "1988-11-23", "gender": "FEMALE", "phone": "9803000002"},
    "2345678903": {"name": "Hari Prasad Koirala", "dob": "1979-02-03", "gender": "MALE", "phone": "9841000003"},
    # Cross-facility demo patients — match Mediciti / Norvic / Pathlabs seeds.
    "2345678909": {"name": "Laxmi Maya Tamang", "dob": "1993-04-14", "gender": "FEMALE", "phone": "9842000001"},
    "2345678910": {"name": "Kiran Bahadur Limbu", "dob": "1985-09-19", "gender": "MALE", "phone": "9842000002"},
    # Expanded federation cohort — MUST match Mediciti / Norvic / Pathlabs / Swastha.
    "2345678911": {"name": "Bishnu Prasad Ghimire", "dob": "1968-03-22", "gender": "MALE", "phone": "9841000011"},
    "2345678912": {"name": "Kamala Devi Bhattarai", "dob": "1974-08-15", "gender": "FEMALE", "phone": "9841000012"},
    "2345678913": {"name": "Suresh Maharjan", "dob": "1982-06-30", "gender": "MALE", "phone": "9841000013"},
    "2345678915": {"name": "Prakash Bahadur Magar", "dob": "1963-11-27", "gender": "MALE", "phone": "9841000015"},
    "2345678918": {"name": "Mina Kumari Adhikari", "dob": "1986-12-12", "gender": "FEMALE", "phone": "9841000018"},
    "2345678919": {"name": "Dipendra Bhandari", "dob": "1971-07-08", "gender": "MALE", "phone": "9841000019"},
    "2345678922": {"name": "Sabina Karki", "dob": "1992-10-03", "gender": "FEMALE", "phone": "9841000022"},
    "2345678924": {"name": "Puja Sharma Poudel", "dob": "1993-06-14", "gender": "FEMALE", "phone": "9841000024"},
    "2345678925": {"name": "Manoj Kumar Tamang", "dob": "1976-03-11", "gender": "MALE", "phone": "9841000025"},
    "2345678927": {"name": "Krishna Bahadur Khadka", "dob": "1966-12-01", "gender": "MALE", "phone": "9841000027"},
    "2345678930": {"name": "Bimala Thapa Chhetri", "dob": "1997-03-28", "gender": "FEMALE", "phone": "9841000030"},
}

# Central Diagnostic (LAB001) comprehensive test menu: distribute panels across
# the three patients with multiple dated visits per panel (series for trends).
REPORTS_LAB001 = [
    # Ram Bahadur (NID 01) — Lipid Profile + Diabetic Profile + LFT
    {
        "nid": "2345678901", "panel": "Lipid Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-08-11", "Dyslipidemia", {
                "Total Cholesterol": "245", "LDL Cholesterol": "165", "HDL Cholesterol": "38", "Triglycerides": "210"}),
            ("2024-02-15", "Dyslipidemia", {
                "Total Cholesterol": "235", "LDL Cholesterol": "155", "HDL Cholesterol": "40", "Triglycerides": "200"}),
            ("2024-07-22", "Improving lipids", {
                "Total Cholesterol": "205", "LDL Cholesterol": "125", "HDL Cholesterol": "45", "Triglycerides": "175"}),
        ],
    },
    {
        "nid": "2345678901", "panel": "Diabetic Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-09-10", "Impaired fasting glucose", {
                "Fasting Blood Sugar": "115", "Postprandial Blood Sugar": "165", "HbA1c": "6.2"}),
            ("2024-03-05", "Pre-diabetes", {
                "Fasting Blood Sugar": "108", "Postprandial Blood Sugar": "155", "HbA1c": "5.9"}),
        ],
    },
    {
        "nid": "2345678901", "panel": "Liver Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2024-01-20", "Mildly elevated transaminases", {
                "Total Bilirubin": "0.9", "Direct Bilirubin": "0.2", "SGPT / ALT": "68", "SGOT / AST": "55",
                "Alkaline Phosphatase": "95", "Total Protein": "7.1", "Albumin": "4.2"}),
        ],
    },
    
    # Sita Kumari (NID 02) — CBC + Thyroid + Iron Studies
    {
        "nid": "2345678902", "panel": "Complete Blood Count", "doctor": "Dr. Gurung",
        "visits": [
            ("2023-05-30", "Mild anemia", {
                "Hemoglobin": "10.5", "Total RBC Count": "4.0", "Total WBC Count": "7500", "Platelet Count": "280",
                "Hematocrit": "33", "MCV": "82", "MCH": "28", "MCHC": "32"}),
            ("2024-02-20", "Mild anemia", {
                "Hemoglobin": "10.8", "Total RBC Count": "4.1", "Total WBC Count": "7200", "Platelet Count": "295",
                "Hematocrit": "34", "MCV": "83", "MCH": "28", "MCHC": "32"}),
            ("2024-08-01", "Improving hemoglobin", {
                "Hemoglobin": "11.4", "Total RBC Count": "4.3", "Total WBC Count": "7800", "Platelet Count": "310",
                "Hematocrit": "36", "MCV": "84", "MCH": "29", "MCHC": "32"}),
        ],
    },
    {
        "nid": "2345678902", "panel": "Thyroid Function Test", "doctor": "Dr. Paudel",
        "visits": [
            ("2023-11-15", "Subclinical hypothyroidism", {
                "TSH": "6.2", "Free T3": "2.8", "Free T4": "0.9"}),
            ("2024-05-10", "Normal on treatment", {
                "TSH": "2.1", "Free T3": "3.1", "Free T4": "1.2"}),
        ],
    },
    {
        "nid": "2345678902", "panel": "Iron Studies", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-03-01", "Iron deficiency", {
                "Serum Iron": "45", "Ferritin": "18", "TIBC": "420"}),
        ],
    },
    
    # Hari Prasad (NID 03) — Cardiac Markers + Electrolyte + Vitamin Assay + Febrile Illness
    {
        "nid": "2345678903", "panel": "Cardiac Markers", "doctor": "Dr. Rai",
        "visits": [
            ("2020-08-10", "Elevated markers", {
                "Troponin I": "0.9", "CK-MB": "8.5", "D-Dimer": "620"}),
            ("2023-06-10", "Elevated markers", {
                "Troponin I": "0.06", "CK-MB": "4.2", "D-Dimer": "580"}),
            ("2024-01-25", "Elevated D-Dimer", {
                "Troponin I": "0.03", "CK-MB": "3.8", "D-Dimer": "820"}),
        ],
    },
    {
        "nid": "2345678903", "panel": "Electrolyte Panel", "doctor": "Dr. Rai",
        "visits": [
            ("2024-02-10", "Mild hypokalemia", {
                "Sodium": "138", "Potassium": "3.3", "Chloride": "102", "Calcium": "9.2"}),
        ],
    },
    {
        "nid": "2345678903", "panel": "Vitamin Assay", "doctor": "Dr. Thapa",
        "visits": [
            ("2024-04-15", "Vitamin D deficiency", {
                "Vitamin D (25-OH)": "18", "Vitamin B12": "320"}),
        ],
    },
    {
        "nid": "2345678903", "panel": "Febrile Illness Panel", "doctor": "Dr. Joshi",
        "visits": [
            ("2024-08-05", "Scrub typhus suspected", {
                "Widal Test": "Negative", "Typhidot IgM": "Negative", "Dengue NS1 Antigen": "Negative",
                "Dengue IgM": "Negative", "Malaria Antigen": "Negative", "Scrub Typhus IgM": "POSITIVE (ELISA)",
                "C-Reactive Protein": "45"}),
        ],
    },

    # Laxmi Maya (NID 09) — thyroid monitoring + anemia work-up
    {
        "nid": "2345678909", "panel": "Thyroid Function Test", "doctor": "Dr. Paudel",
        "visits": [
            ("2023-12-08", "Subclinical hypothyroidism", {
                "TSH": "7.1", "Free T3": "2.9", "Free T4": "1.0"}),
            ("2024-06-11", "Improved on levothyroxine", {
                "TSH": "3.8", "Free T3": "3.0", "Free T4": "1.2"}),
        ],
    },
    {
        "nid": "2345678909", "panel": "Complete Blood Count", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-04-12", "Mild anemia", {
                "Hemoglobin": "10.9", "Total RBC Count": "3.9", "Total WBC Count": "6100", "Platelet Count": "265",
                "Hematocrit": "34", "MCV": "81", "MCH": "27", "MCHC": "33"}),
        ],
    },
    {
        "nid": "2345678909", "panel": "Iron Studies", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-04-12", "Iron deficiency", {
                "Serum Iron": "50", "Ferritin": "21", "TIBC": "435"}),
        ],
    },

    # Kiran Bahadur (NID 10) — diabetes control + lipids + early renal check
    {
        "nid": "2345678910", "panel": "Diabetic Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-06-10", "Poorly controlled diabetes", {
                "Fasting Blood Sugar": "152", "Postprandial Blood Sugar": "226", "HbA1c": "8.0"}),
            ("2024-02-14", "Improving control", {
                "Fasting Blood Sugar": "124", "Postprandial Blood Sugar": "172", "HbA1c": "7.1"}),
            ("2024-08-15", "Continued improvement", {
                "Fasting Blood Sugar": "118", "Postprandial Blood Sugar": "158", "HbA1c": "6.8"}),
        ],
    },
    {
        "nid": "2345678910", "panel": "Lipid Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-06-10", "Dyslipidemia", {
                "Total Cholesterol": "240", "LDL Cholesterol": "162", "HDL Cholesterol": "37", "Triglycerides": "222"}),
            ("2024-08-15", "On statin", {
                "Total Cholesterol": "198", "LDL Cholesterol": "118", "HDL Cholesterol": "42", "Triglycerides": "168"}),
        ],
    },
    {
        "nid": "2345678910", "panel": "Renal Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2024-05-12", "Mildly elevated creatinine", {
                "Urea": "48", "Blood Urea Nitrogen": "22", "Creatinine": "1.4", "Uric Acid": "7.8"}),
        ],
    },

    # ---------------- Expanded federation cohort (NIDs ...11 .. ...30) ----------------
    # Bishnu (NID 11) — diabetic control + renal decline mirroring Mediciti's trend
    {
        "nid": "2345678911", "panel": "Diabetic Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2022-09-14", "Uncontrolled diabetes", {
                "Fasting Blood Sugar": "196", "Postprandial Blood Sugar": "268", "HbA1c": "8.9"}),
            ("2023-04-20", "Improving on metformin", {
                "Fasting Blood Sugar": "174", "Postprandial Blood Sugar": "232", "HbA1c": "8.1"}),
            ("2024-04-24", "Approaching target", {
                "Fasting Blood Sugar": "152", "Postprandial Blood Sugar": "198", "HbA1c": "7.4"}),
        ],
    },
    {
        "nid": "2345678911", "panel": "Renal Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2023-10-16", "Early diabetic nephropathy", {
                "Urea": "44", "Blood Urea Nitrogen": "21", "Creatinine": "1.3", "Uric Acid": "7.4"}),
            ("2024-06-22", "Progressive nephropathy", {
                "Urea": "56", "Blood Urea Nitrogen": "26", "Creatinine": "1.7", "Uric Acid": "7.9"}),
        ],
    },
    # Kamala (NID 12) — thyroid + anemia recovery series
    {
        "nid": "2345678912", "panel": "Thyroid Function Test", "doctor": "Dr. Rai",
        "visits": [
            ("2022-11-10", "Overt hypothyroidism", {
                "TSH": "11.4", "Free T3": "2.0", "Free T4": "0.6"}),
            ("2023-06-17", "Improving on levothyroxine", {
                "TSH": "6.2", "Free T3": "2.5", "Free T4": "0.9"}),
            ("2024-05-11", "Euthyroid on treatment", {
                "TSH": "3.1", "Free T3": "3.0", "Free T4": "1.2"}),
        ],
    },
    {
        "nid": "2345678912", "panel": "Complete Blood Count", "doctor": "Dr. Gurung",
        "visits": [
            ("2022-11-10", "Microcytic anemia", {
                "Hemoglobin": "9.6", "Total RBC Count": "3.9", "Total WBC Count": "6800", "Platelet Count": "302",
                "Hematocrit": "30", "MCV": "74", "MCH": "24", "MCHC": "30"}),
            ("2024-05-11", "Anemia resolving", {
                "Hemoglobin": "11.9", "Total RBC Count": "4.4", "Total WBC Count": "7100", "Platelet Count": "288",
                "Hematocrit": "36", "MCV": "82", "MCH": "27", "MCHC": "32"}),
        ],
    },
    {
        "nid": "2345678912", "panel": "Iron Studies", "doctor": "Dr. Gurung",
        "visits": [
            ("2022-11-10", "Iron deficiency", {
                "Serum Iron": "34", "Ferritin": "9", "TIBC": "438"}),
            ("2024-05-11", "Iron stores replete", {
                "Serum Iron": "72", "Ferritin": "34", "TIBC": "362"}),
        ],
    },
    # Suresh (NID 13) — lipid + LFT improvement on statin and weight loss
    {
        "nid": "2345678913", "panel": "Lipid Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-02-22", "Mixed dyslipidemia", {
                "Total Cholesterol": "262", "LDL Cholesterol": "178", "HDL Cholesterol": "34", "Triglycerides": "286"}),
            ("2023-09-27", "Partial response", {
                "Total Cholesterol": "228", "LDL Cholesterol": "148", "HDL Cholesterol": "38", "Triglycerides": "218"}),
            ("2024-08-14", "Good response to statin", {
                "Total Cholesterol": "192", "LDL Cholesterol": "112", "HDL Cholesterol": "44", "Triglycerides": "158"}),
        ],
    },
    {
        "nid": "2345678913", "panel": "Liver Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2023-09-27", "Transaminitis consistent with NAFLD", {
                "Total Bilirubin": "1.0", "Direct Bilirubin": "0.3", "SGPT / ALT": "86", "SGOT / AST": "64",
                "Alkaline Phosphatase": "132", "Total Protein": "7.4", "Albumin": "4.3"}),
            ("2024-08-14", "Transaminases normalized", {
                "Total Bilirubin": "0.9", "Direct Bilirubin": "0.2", "SGPT / ALT": "52", "SGOT / AST": "38",
                "Alkaline Phosphatase": "112", "Total Protein": "7.2", "Albumin": "4.4"}),
        ],
    },
    # Prakash (NID 15) — post-MI lipid control + cardiac markers
    {
        "nid": "2345678915", "panel": "Lipid Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-03-16", "Dyslipidemia in established CAD", {
                "Total Cholesterol": "236", "LDL Cholesterol": "158", "HDL Cholesterol": "35", "Triglycerides": "204"}),
            ("2024-07-21", "At target on high-dose statin", {
                "Total Cholesterol": "168", "LDL Cholesterol": "84", "HDL Cholesterol": "42", "Triglycerides": "148"}),
        ],
    },
    {
        "nid": "2345678915", "panel": "Cardiac Markers", "doctor": "Dr. Rai",
        "visits": [
            ("2024-07-21", "No acute myocardial injury; raised D-Dimer", {
                "Troponin I": "0.03", "CK-MB": "3.4", "D-Dimer": "680"}),
        ],
    },
    # Mina (NID 18) — thyroid normalization + healthy renal baseline
    {
        "nid": "2345678918", "panel": "Thyroid Function Test", "doctor": "Dr. Rai",
        "visits": [
            ("2023-02-01", "Hypothyroidism", {
                "TSH": "9.8", "Free T3": "2.2", "Free T4": "0.7"}),
            ("2024-02-14", "Euthyroid on levothyroxine", {
                "TSH": "3.6", "Free T3": "3.1", "Free T4": "1.1"}),
        ],
    },
    {
        "nid": "2345678918", "panel": "Renal Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2024-02-14", "Normal renal function", {
                "Urea": "30", "Blood Urea Nitrogen": "14", "Creatinine": "0.9", "Uric Acid": "5.1"}),
        ],
    },
    # Dipendra (NID 19) — CKD progression with worsening anemia
    {
        "nid": "2345678919", "panel": "Renal Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2022-08-19", "CKD stage 3 with hyperuricemia", {
                "Urea": "58", "Blood Urea Nitrogen": "27", "Creatinine": "1.8", "Uric Acid": "8.9"}),
            ("2023-03-24", "Declining function", {
                "Urea": "70", "Blood Urea Nitrogen": "33", "Creatinine": "2.2", "Uric Acid": "9.4"}),
            ("2024-09-06", "Further decline", {
                "Urea": "84", "Blood Urea Nitrogen": "39", "Creatinine": "2.7", "Uric Acid": "8.6"}),
        ],
    },
    {
        "nid": "2345678919", "panel": "Complete Blood Count", "doctor": "Dr. Gurung",
        "visits": [
            ("2023-03-24", "Anemia of chronic kidney disease", {
                "Hemoglobin": "10.2", "Total RBC Count": "3.7", "Total WBC Count": "7400", "Platelet Count": "244",
                "Hematocrit": "31", "MCV": "86", "MCH": "28", "MCHC": "32"}),
            ("2024-09-06", "Worsening renal anemia", {
                "Hemoglobin": "9.3", "Total RBC Count": "3.4", "Total WBC Count": "7100", "Platelet Count": "236",
                "Hematocrit": "28", "MCV": "85", "MCH": "28", "MCHC": "32"}),
        ],
    },
    {
        "nid": "2345678919", "panel": "Electrolyte Panel", "doctor": "Dr. Paudel",
        "visits": [
            ("2024-09-06", "Hyperkalemia in CKD", {
                "Sodium": "137", "Potassium": "5.4", "Chloride": "105", "Calcium": "8.4"}),
        ],
    },
    # Sabina (NID 22) — PCOS metabolic screen + vitamin deficiency
    {
        "nid": "2345678922", "panel": "Diabetic Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-07-13", "Insulin resistance / pre-diabetes", {
                "Fasting Blood Sugar": "104", "Postprandial Blood Sugar": "148", "HbA1c": "5.8"}),
            ("2024-06-20", "Normoglycemic on metformin", {
                "Fasting Blood Sugar": "94", "Postprandial Blood Sugar": "126", "HbA1c": "5.4"}),
        ],
    },
    {
        "nid": "2345678922", "panel": "Thyroid Function Test", "doctor": "Dr. Rai",
        "visits": [
            ("2023-07-13", "Subclinical hypothyroidism", {
                "TSH": "5.8", "Free T3": "2.8", "Free T4": "1.0"}),
            ("2024-06-20", "Normalized TSH", {
                "TSH": "3.9", "Free T3": "3.0", "Free T4": "1.1"}),
        ],
    },
    {
        "nid": "2345678922", "panel": "Vitamin Assay", "doctor": "Dr. Thapa",
        "visits": [
            ("2023-07-13", "Vitamin D deficiency", {
                "Vitamin D (25-OH)": "14", "Vitamin B12": "310"}),
            ("2024-06-20", "Vitamin D repleted", {
                "Vitamin D (25-OH)": "36", "Vitamin B12": "420"}),
        ],
    },
    # Puja (NID 24) — postpartum anemia work-up (Norvic patient, labs here)
    {
        "nid": "2345678924", "panel": "Complete Blood Count", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-02-21", "Moderate microcytic anemia", {
                "Hemoglobin": "9.4", "Total RBC Count": "3.8", "Total WBC Count": "8200", "Platelet Count": "298",
                "Hematocrit": "30", "MCV": "76", "MCH": "25", "MCHC": "31"}),
            ("2024-09-12", "Anemia corrected", {
                "Hemoglobin": "11.8", "Total RBC Count": "4.5", "Total WBC Count": "7600", "Platelet Count": "264",
                "Hematocrit": "36", "MCV": "84", "MCH": "28", "MCHC": "33"}),
        ],
    },
    {
        "nid": "2345678924", "panel": "Iron Studies", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-02-21", "Depleted iron stores", {
                "Serum Iron": "31", "Ferritin": "7", "TIBC": "462"}),
            ("2024-09-12", "Iron replete", {
                "Serum Iron": "84", "Ferritin": "42", "TIBC": "348"}),
        ],
    },
    # Manoj (NID 25) — scrub typhus AKI recovery (LFT + renal at Central)
    {
        "nid": "2345678925", "panel": "Liver Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2024-09-18", "Rickettsial hepatitis", {
                "Total Bilirubin": "1.6", "Direct Bilirubin": "0.6", "SGPT / ALT": "108", "SGOT / AST": "126",
                "Alkaline Phosphatase": "164", "Total Protein": "6.6", "Albumin": "3.1"}),
            ("2024-09-24", "Recovering", {
                "Total Bilirubin": "1.0", "Direct Bilirubin": "0.3", "SGPT / ALT": "64", "SGOT / AST": "58",
                "Alkaline Phosphatase": "128", "Total Protein": "6.9", "Albumin": "3.6"}),
        ],
    },
    {
        "nid": "2345678925", "panel": "Renal Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2024-09-18", "Acute kidney injury", {
                "Urea": "78", "Blood Urea Nitrogen": "36", "Creatinine": "2.4", "Uric Acid": "8.2"}),
            ("2024-09-24", "AKI resolving with hydration", {
                "Urea": "40", "Blood Urea Nitrogen": "19", "Creatinine": "1.3", "Uric Acid": "6.4"}),
        ],
    },
    # Krishna (NID 27) — 4-source star: long diabetic + lipid series at Central
    {
        "nid": "2345678927", "panel": "Diabetic Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2021-05-21", "Poorly controlled diabetes", {
                "Fasting Blood Sugar": "212", "Postprandial Blood Sugar": "298", "HbA1c": "9.6"}),
            ("2022-06-24", "Improving", {
                "Fasting Blood Sugar": "188", "Postprandial Blood Sugar": "262", "HbA1c": "8.8"}),
            ("2023-07-15", "Continued improvement", {
                "Fasting Blood Sugar": "164", "Postprandial Blood Sugar": "224", "HbA1c": "8.0"}),
            ("2024-07-28", "Near target", {
                "Fasting Blood Sugar": "142", "Postprandial Blood Sugar": "192", "HbA1c": "7.2"}),
        ],
    },
    {
        "nid": "2345678927", "panel": "Lipid Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2021-05-21", "Severe mixed dyslipidemia", {
                "Total Cholesterol": "268", "LDL Cholesterol": "184", "HDL Cholesterol": "32", "Triglycerides": "264"}),
            ("2024-07-28", "Controlled on statin", {
                "Total Cholesterol": "196", "LDL Cholesterol": "116", "HDL Cholesterol": "41", "Triglycerides": "162"}),
        ],
    },
    # Bimala (NID 30) — young-adult anemia + vitamin deficiency screen
    {
        "nid": "2345678930", "panel": "Complete Blood Count", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-01-20", "Microcytic hypochromic anemia", {
                "Hemoglobin": "10.4", "Total RBC Count": "4.1", "Total WBC Count": "6900", "Platelet Count": "312",
                "Hematocrit": "33", "MCV": "77", "MCH": "25", "MCHC": "31"}),
            ("2024-08-08", "Improved on oral iron", {
                "Hemoglobin": "12.2", "Total RBC Count": "4.5", "Total WBC Count": "7200", "Platelet Count": "286",
                "Hematocrit": "37", "MCV": "83", "MCH": "28", "MCHC": "33"}),
        ],
    },
    {
        "nid": "2345678930", "panel": "Vitamin Assay", "doctor": "Dr. Thapa",
        "visits": [
            ("2024-01-20", "Severe vitamin D deficiency", {
                "Vitamin D (25-OH)": "11", "Vitamin B12": "268"}),
            ("2024-08-08", "Vitamin D corrected", {
                "Vitamin D (25-OH)": "34", "Vitamin B12": "412"}),
        ],
    },
    {
        "nid": "2345678930", "panel": "Thyroid Function Test", "doctor": "Dr. Rai",
        "visits": [
            ("2024-01-20", "Subclinical hypothyroidism", {
                "TSH": "5.4", "Free T3": "2.9", "Free T4": "1.0"}),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed Central Diagnostic Laboratory with comprehensive demo reports."

    def handle(self, *args, **options):
        if ORG_CODE != "LAB001":
            self.stdout.write(self.style.WARNING(f"This seed is for LAB001, not {ORG_CODE}"))
            return

        for row in REPORTS_LAB001:
            demo = DEMOGRAPHICS[row["nid"]]
            patient = self._make_patient(row["nid"], demo)
            meta = {"nid": row["nid"], "full_name": demo["name"], "date_of_birth": demo["dob"],
                    "gender": demo["gender"], "phone": demo["phone"]}
            panel_name = row["panel"]

            for date, conclusion, values_dict in row["visits"]:
                report = self._make_report(patient, panel_name, row["doctor"], date, conclusion)
                for analyte_name, value_str in values_dict.items():
                    self._make_result(report, analyte_name, value_str)
                status_code, _ = services.push_index(
                    row["nid"], meta, "DiagnosticReport", report.id, date, panel_name)
                self.stdout.write(f"  {panel_name} @ {date} -> index {status_code}")

        self.stdout.write(self.style.SUCCESS(f"Seeded {settings.ORG_NAME} ({ORG_CODE})."))

    def _make_patient(self, nid, demo):
        defaults = {"dob": demo["dob"], "gender": demo["gender"], "phone": demo["phone"],
                    "patient_name": demo["name"]}
        patient, _ = LabPatient.objects.get_or_create(nid=nid, defaults=defaults)
        return patient

    def _make_report(self, patient, panel_name, doctor, date, conclusion):
        obj, _ = LabReport.objects.get_or_create(
            patient=patient, panel_name=panel_name, report_date=date,
            defaults={"ordering_doctor": doctor, "conclusion": conclusion})
        return obj

    def _make_result(self, report, analyte_name, value_str):
        meta = catalog.analyte_meta(analyte_name)
        unit = meta.get("unit", "")
        range_low = meta.get("low")
        range_high = meta.get("high")
        if range_low is not None and range_high is not None:
            range_str = f"{range_low}-{range_high}"
        elif range_low is not None:
            range_str = f">{range_low}"
        elif range_high is not None:
            range_str = f"<{range_high}"
        else:
            range_str = ""
        
        obj, _ = LabResult.objects.get_or_create(
            report=report, analyte=analyte_name,
            defaults={"result_value": value_str, "units": unit, "reference_range": range_str})
        return obj
