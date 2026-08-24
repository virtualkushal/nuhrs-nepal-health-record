"""
Rich, realistic seed for Nepal Mediciti Hospital.

Builds a full hospital record for 6 patients across multiple departments:
  * rich demographics (blood group, allergies, address, emergency contact)
  * encounters tagged by department
  * conditions (ICD-10)
  * nurse-recorded vitals
  * lab orders -> reports -> results (LOINC + reference range + interpretation),
    as multi-date SERIES so trend charts render
  * medication requests (prescriptions)

Every writer is IDEMPOTENT (get_or_create keyed on natural keys) so re-running
this command NEVER duplicates rows. Safe to run repeatedly.

Run:  python manage.py seed
"""
from django.core.management.base import BaseCommand

from clinical import services
from clinical.models import (
    Allergy,
    Condition,
    Encounter,
    LabOrder,
    LabReport,
    LabResult,
    LocalPatient,
    MedicationRequest,
    Vitals,
)

# Lab panel catalogue: panel -> list of (test, LOINC, unit, ref_range, normal)
PANELS = {
    "Complete Blood Count": [
        ("Hemoglobin", "718-7", "g/dL", "13.0-17.0", "14.5"),
        ("Total WBC Count", "6690-2", "10^3/uL", "4.0-11.0", "7.2"),
        ("Platelet Count", "777-3", "10^3/uL", "150-400", "250"),
        ("Hematocrit", "4544-3", "%", "40-50", "44"),
        ("RBC Count", "789-8", "10^6/uL", "4.5-5.9", "5.0"),
    ],
    "Lipid Profile": [
        ("Total Cholesterol", "2093-3", "mg/dL", "<200", "180"),
        ("LDL Cholesterol", "13457-7", "mg/dL", "<100", "90"),
        ("HDL Cholesterol", "2085-9", "mg/dL", ">40", "48"),
        ("Triglycerides", "2571-8", "mg/dL", "<150", "120"),
    ],
    "Renal Function Test": [
        ("Blood Urea", "3094-0", "mg/dL", "15-40", "28"),
        ("Serum Creatinine", "2160-0", "mg/dL", "0.7-1.3", "1.0"),
        ("Uric Acid", "3084-1", "mg/dL", "3.5-7.2", "5.0"),
        ("eGFR", "33914-3", "mL/min", ">90", "95"),
    ],
    "Liver Function Test": [
        ("SGPT (ALT)", "1742-6", "U/L", "7-56", "30"),
        ("SGOT (AST)", "1920-8", "U/L", "5-40", "25"),
        ("Alkaline Phosphatase", "6768-6", "U/L", "44-147", "90"),
        ("Total Bilirubin", "1975-2", "mg/dL", "0.1-1.2", "0.8"),
        ("Serum Albumin", "1751-7", "g/dL", "3.5-5.0", "4.2"),
    ],
    "Blood Sugar": [
        ("Fasting Blood Glucose", "1558-6", "mg/dL", "70-100", "92"),
        ("HbA1c", "4548-4", "%", "4.0-5.6", "5.3"),
        ("Postprandial Glucose", "1521-4", "mg/dL", "<140", "120"),
    ],
    "Thyroid Function Test": [
        ("TSH", "3016-3", "uIU/mL", "0.4-4.0", "2.1"),
        ("Free T3", "3051-0", "pg/mL", "2.3-4.2", "3.1"),
        ("Free T4", "3024-7", "ng/dL", "0.8-1.8", "1.2"),
    ],
    "Cardiac Markers": [
        ("Troponin I", "10839-9", "ng/mL", "<0.04", "0.02"),
        ("CK-MB", "13969-1", "ng/mL", "<5.0", "2.5"),
        ("CRP", "1988-5", "mg/L", "<3.0", "1.5"),
    ],
    "Electrolytes": [
        ("Sodium", "2951-2", "mmol/L", "135-145", "140"),
        ("Potassium", "2823-3", "mmol/L", "3.5-5.1", "4.2"),
        ("Chloride", "2075-0", "mmol/L", "98-107", "102"),
    ],
    "Coagulation Profile": [
        ("Prothrombin Time", "5902-2", "sec", "11-13.5", "12.0"),
        ("INR", "6301-6", "", "0.8-1.1", "1.0"),
        ("APTT", "3173-2", "sec", "25-35", "30"),
    ],
    "Serology": [
        ("Dengue NS1 Antigen", "", "", "Negative", "Negative"),
        ("HBsAg", "5195-3", "", "Negative", "Negative"),
        ("Widal Test", "", "", "Negative", "Negative"),
    ],
    "Iron Studies": [
        ("Serum Iron", "2498-4", "ug/dL", "60-170", "100"),
        ("Ferritin", "2276-4", "ng/mL", "30-400", "150"),
        ("TIBC", "2500-7", "ug/dL", "240-450", "330"),
    ],
    "Urine Routine": [
        ("Urine Protein", "2888-6", "", "Negative", "Negative"),
        ("Urine Glucose", "2350-7", "", "Negative", "Negative"),
        ("Urine Pus Cells", "", "/hpf", "0-5", "2"),
    ],
}

# Canonical demographics — NIDs 901..903 MUST match other services.
PATIENTS = {
    "2345678901": dict(
        name="Ram Bahadur Thapa", dob="1970-05-12", gender="MALE", phone="9841000001",
        address="Kupondole, Lalitpur", blood_group="O+", marital="Married",
        occupation="Retired Teacher", ethnicity="Chhetri",
        ec_name="Sita Thapa", ec_phone="9800000011",
        allergies=[("Penicillin", "Skin rash", "moderate", "2015-04-10")],
    ),
    "2345678902": dict(
        name="Sita Kumari Sharma", dob="1988-11-23", gender="FEMALE", phone="9803000002",
        address="Baneshwor, Kathmandu", blood_group="A+", marital="Married",
        occupation="Bank Officer", ethnicity="Brahmin",
        ec_name="Gopal Sharma", ec_phone="9800000022",
        allergies=[],
    ),
    "2345678903": dict(
        name="Hari Prasad Koirala", dob="1979-02-03", gender="MALE", phone="9841000003",
        address="Biratnagar, Morang", blood_group="B+", marital="Married",
        occupation="Businessman", ethnicity="Brahmin",
        ec_name="Radha Koirala", ec_phone="9800000033",
        allergies=[("Sulfonamides", "Urticaria", "severe", "2018-09-01")],
    ),
    "2345678904": dict(
        name="Gita Devi Rai", dob="1996-07-19", gender="FEMALE", phone="9812000004",
        address="Dharan, Sunsari", blood_group="O-", marital="Single",
        occupation="Student", ethnicity="Rai",
        ec_name="Man Bahadur Rai", ec_phone="9800000044",
        allergies=[],
    ),
    "2345678905": dict(
        name="Bikash Shrestha", dob="1962-01-30", gender="MALE", phone="9856000005",
        address="Pokhara, Kaski", blood_group="AB+", marital="Married",
        occupation="Farmer", ethnicity="Newar",
        ec_name="Kamala Shrestha", ec_phone="9800000055",
        allergies=[],
    ),
    "2345678906": dict(
        name="Maya Gurung", dob="1975-10-08", gender="FEMALE", phone="9846000006",
        address="Lakeside, Pokhara", blood_group="B-", marital="Widowed",
        occupation="Hotel Owner", ethnicity="Gurung",
        ec_name="Anil Gurung", ec_phone="9800000066",
        allergies=[("Aspirin", "Bronchospasm", "moderate", "2019-03-15")],
    ),
    # --- Cross-facility demo patients (NIDs ...09/.10 match Norvic + both labs) ---
    "2345678909": dict(
        name="Laxmi Maya Tamang", dob="1993-04-14", gender="FEMALE", phone="9842000001",
        address="Jhamsikhel, Lalitpur", blood_group="O+", marital="Single",
        occupation="Registered Nurse", ethnicity="Tamang",
        ec_name="Sunita Tamang", ec_phone="9800000099",
        allergies=[("Penicillin", "Skin rash", "moderate", "2015-02-10")],
    ),
    "2345678910": dict(
        name="Kiran Bahadur Limbu", dob="1985-09-19", gender="MALE", phone="9842000002",
        address="Sundhara, Kathmandu", blood_group="A+", marital="Married",
        occupation="IT Manager", ethnicity="Limbu",
        ec_name="Roshni Limbu", ec_phone="9800000100",
        allergies=[("Iodinated contrast dye", "Urticaria", "mild", "2020-08-01")],
    ),
}

# Clinical journeys.  Each episode:
#   department, doctor, date, type, reason,
#   conditions: [(text, icd10, onset)],
#   vitals: {sbp,dbp,pulse,temp,spo2,rr,height,weight,bmi},
#   labs: [(panel, date, {test: (value, interp)})],  (interp: H/L/N/A)
#   meds: [(name, rxnorm, dose, freq, route, duration)]
JOURNEYS = {
    "2345678901": [  # Ram — diabetes -> nephropathy -> anemia -> dyslipidemia
        dict(
            department="Internal Medicine & Endocrinology", doctor="Dr. Anil Karki",
            date="2023-01-15", type="OPD", reason="Follow-up diabetes",
            conditions=[("Type 2 Diabetes Mellitus", "E11.9", "2021-06-01"),
                        ("Dyslipidemia", "E78.5", "2022-02-10"),
                        ("Essential Hypertension", "I10", "2022-02-10")],
            vitals=dict(sbp=138, dbp=88, pulse=78, temp=36.7, spo2=98, rr=16, height=168, weight=74, bmi=26.2),
            labs=[
                ("Blood Sugar", "2023-01-15", {"Fasting Blood Glucose": ("178", "H"), "HbA1c": ("7.9", "H"), "Postprandial Glucose": ("236", "H")}),
                ("Blood Sugar", "2023-06-20", {"Fasting Blood Glucose": ("186", "H"), "HbA1c": ("8.1", "H"), "Postprandial Glucose": ("248", "H")}),
                ("Blood Sugar", "2023-12-05", {"Fasting Blood Glucose": ("190", "H"), "HbA1c": ("8.6", "H"), "Postprandial Glucose": ("255", "H")}),
                ("Blood Sugar", "2024-06-14", {"Fasting Blood Glucose": ("172", "H"), "HbA1c": ("7.6", "H"), "Postprandial Glucose": ("210", "H")}),
                ("Lipid Profile", "2023-01-15", {"Total Cholesterol": ("232", "H"), "LDL Cholesterol": ("158", "H"), "HDL Cholesterol": ("38", "L"), "Triglycerides": ("210", "H")}),
            ],
            meds=[("Metformin", "6809", "500 mg", "twice daily", "oral", "ongoing"),
                  ("Atorvastatin", "83367", "20 mg", "once daily at night", "oral", "ongoing"),
                  ("Losartan", "52175", "50 mg", "once daily", "oral", "ongoing")],
        ),
        dict(
            department="Nephrology & Kidney Transplantation", doctor="Dr. Sabina Rana",
            date="2024-03-01", type="OPD", reason="Rising creatinine",
            conditions=[("Diabetic Nephropathy", "E11.21", "2023-11-20"),
                        ("Iron Deficiency Anemia", "D50.9", "2024-03-01")],
            vitals=dict(sbp=146, dbp=90, pulse=82, temp=36.6, spo2=97, rr=18, height=168, weight=72, bmi=25.5),
            labs=[
                ("Renal Function Test", "2023-11-20", {"Serum Creatinine": ("1.2", "N"), "Blood Urea": ("42", "H"), "eGFR": ("72", "L")}),
                ("Renal Function Test", "2024-03-01", {"Serum Creatinine": ("1.6", "H"), "Blood Urea": ("54", "H"), "eGFR": ("55", "L")}),
                ("Renal Function Test", "2024-08-05", {"Serum Creatinine": ("1.9", "H"), "Blood Urea": ("62", "H"), "eGFR": ("46", "L")}),
                ("Complete Blood Count", "2024-03-01", {"Hemoglobin": ("10.8", "L"), "Hematocrit": ("33", "L")}),
                ("Iron Studies", "2024-03-01", {"Serum Iron": ("42", "L"), "Ferritin": ("18", "L"), "TIBC": ("410", "N")}),
                ("Urine Routine", "2024-03-01", {"Urine Protein": ("++", "A"), "Urine Glucose": ("+", "A")}),
            ],
            meds=[("Ferrous Sulfate", "310965", "200 mg", "twice daily", "oral", "3 months"),
                  ("Furosemide", "4603", "40 mg", "once daily", "oral", "ongoing")],
        ),
    ],
    "2345678902": [  # Sita — hypertension + hypothyroidism + asthma
        dict(
            department="Internal Medicine & Endocrinology", doctor="Dr. Anil Karki",
            date="2022-03-15", type="OPD", reason="Fatigue, weight gain",
            conditions=[("Essential Hypertension", "I10", "2022-03-15"),
                        ("Hypothyroidism", "E03.9", "2022-03-15"),
                        ("Obesity", "E66.9", "2022-03-15")],
            vitals=dict(sbp=148, dbp=92, pulse=68, temp=36.5, spo2=99, rr=15, height=158, weight=78, bmi=31.2),
            labs=[
                ("Thyroid Function Test", "2022-03-15", {"TSH": ("8.6", "H"), "Free T4": ("0.6", "L"), "Free T3": ("2.1", "L")}),
                ("Thyroid Function Test", "2023-02-10", {"TSH": ("5.2", "H"), "Free T4": ("0.9", "N"), "Free T3": ("2.6", "N")}),
                ("Thyroid Function Test", "2024-02-05", {"TSH": ("3.4", "N"), "Free T4": ("1.1", "N"), "Free T3": ("3.0", "N")}),
                ("Lipid Profile", "2022-03-15", {"Total Cholesterol": ("214", "H"), "LDL Cholesterol": ("140", "H")}),
            ],
            meds=[("Levothyroxine", "10582", "75 mcg", "once daily before breakfast", "oral", "ongoing"),
                  ("Amlodipine", "17767", "5 mg", "once daily", "oral", "ongoing")],
        ),
        dict(
            department="Pulmonary, Critical Care & Sleep Medicine", doctor="Dr. Prakash Thapa",
            date="2023-08-22", type="OPD", reason="Wheezing, breathlessness",
            conditions=[("Bronchial Asthma", "J45.9", "2023-08-22")],
            vitals=dict(sbp=132, dbp=84, pulse=88, temp=36.8, spo2=95, rr=22, height=158, weight=77, bmi=30.8),
            labs=[],
            meds=[("Salbutamol Inhaler", "435", "100 mcg", "2 puffs as needed", "inhalation", "ongoing"),
                  ("Budesonide Inhaler", "1808", "200 mcg", "twice daily", "inhalation", "ongoing")],
        ),
    ],
    "2345678903": [  # Hari — cardiology + diabetes + COPD
        dict(
            department="Cardiology", doctor="Dr. Rajesh Malla",
            date="2020-08-10", type="OPD", reason="Chest pain on exertion",
            conditions=[("Ischemic Heart Disease", "I25.9", "2020-08-10"),
                        ("Type 2 Diabetes Mellitus", "E11.9", "2019-05-01")],
            vitals=dict(sbp=140, dbp=86, pulse=80, temp=36.6, spo2=97, rr=17, height=172, weight=80, bmi=27.0),
            labs=[
                ("Lipid Profile", "2020-08-10", {"Total Cholesterol": ("248", "H"), "LDL Cholesterol": ("170", "H"), "HDL Cholesterol": ("34", "L"), "Triglycerides": ("230", "H")}),
                ("Lipid Profile", "2023-06-10", {"Total Cholesterol": ("212", "H"), "LDL Cholesterol": ("138", "H"), "HDL Cholesterol": ("40", "N")}),
                ("Blood Sugar", "2020-08-10", {"Fasting Blood Glucose": ("162", "H"), "HbA1c": ("7.4", "H")}),
            ],
            meds=[("Aspirin", "1191", "75 mg", "once daily", "oral", "ongoing"),
                  ("Clopidogrel", "32968", "75 mg", "once daily", "oral", "ongoing"),
                  ("Metoprolol", "6918", "50 mg", "twice daily", "oral", "ongoing"),
                  ("Atorvastatin", "83367", "40 mg", "once daily at night", "oral", "ongoing")],
        ),
        dict(
            department="Emergency Medicine And Pre-Hospital Care", doctor="Dr. Nabin Adhikari",
            date="2024-01-22", type="Emergency", reason="Acute chest pain, diaphoresis",
            conditions=[("Acute Myocardial Infarction", "I21.9", "2024-01-22"),
                        ("Heart Failure", "I50.9", "2024-01-25")],
            vitals=dict(sbp=158, dbp=98, pulse=104, temp=36.9, spo2=92, rr=24, height=172, weight=79, bmi=26.7),
            labs=[
                ("Cardiac Markers", "2024-01-22", {"Troponin I": ("3.8", "H"), "CK-MB": ("28", "H"), "CRP": ("12", "H")}),
                ("Cardiac Markers", "2024-01-23", {"Troponin I": ("5.2", "H"), "CK-MB": ("34", "H")}),
                ("Electrolytes", "2024-01-22", {"Sodium": ("138", "N"), "Potassium": ("4.6", "N")}),
            ],
            meds=[("Enoxaparin", "67108", "60 mg", "twice daily", "subcutaneous", "5 days"),
                  ("Furosemide", "4603", "40 mg", "twice daily", "IV", "3 days")],
        ),
        dict(
            department="Pulmonary, Critical Care & Sleep Medicine", doctor="Dr. Prakash Thapa",
            date="2022-11-05", type="OPD", reason="Chronic cough, breathlessness",
            conditions=[("Chronic Obstructive Pulmonary Disease", "J44.9", "2022-11-05")],
            vitals=dict(sbp=136, dbp=84, pulse=90, temp=36.7, spo2=93, rr=23, height=172, weight=78, bmi=26.4),
            labs=[],
            meds=[("Tiotropium Inhaler", "69420", "18 mcg", "once daily", "inhalation", "ongoing")],
        ),
    ],
    "2345678904": [  # Gita — emergency dengue + anemia + thrombocytopenia
        dict(
            department="Emergency Medicine And Pre-Hospital Care", doctor="Dr. Nabin Adhikari",
            date="2024-09-10", type="Emergency", reason="High fever, body ache, rash",
            conditions=[("Dengue Fever", "A90", "2024-09-10"),
                        ("Thrombocytopenia", "D69.6", "2024-09-11"),
                        ("Iron Deficiency Anemia", "D50.9", "2024-09-10")],
            vitals=dict(sbp=102, dbp=64, pulse=98, temp=39.4, spo2=97, rr=20, height=160, weight=52, bmi=20.3),
            labs=[
                ("Serology", "2024-09-10", {"Dengue NS1 Antigen": ("Positive", "A")}),
                ("Complete Blood Count", "2024-09-10", {"Platelet Count": ("95", "L"), "Hemoglobin": ("10.2", "L"), "Hematocrit": ("41", "N"), "Total WBC Count": ("3.2", "L")}),
                ("Complete Blood Count", "2024-09-12", {"Platelet Count": ("62", "L"), "Hemoglobin": ("10.0", "L"), "Total WBC Count": ("2.9", "L")}),
                ("Complete Blood Count", "2024-09-14", {"Platelet Count": ("110", "L"), "Hemoglobin": ("10.5", "L"), "Total WBC Count": ("4.1", "N")}),
                ("Iron Studies", "2024-09-14", {"Serum Iron": ("48", "L"), "Ferritin": ("22", "L")}),
            ],
            meds=[("Paracetamol", "161", "500 mg", "every 6 hours as needed", "oral", "5 days"),
                  ("Oral Rehydration Salts", "8591", "1 sachet", "after each loose stool", "oral", "as needed")],
        ),
        dict(
            department="Emergency Medicine And Pre-Hospital Care", doctor="Dr. Nabin Adhikari",
            date="2023-05-18", type="Emergency", reason="Fever, abdominal pain",
            conditions=[("Typhoid Fever", "A01.0", "2023-05-18"),
                        ("Acute Gastroenteritis", "A09", "2023-05-18")],
            vitals=dict(sbp=108, dbp=70, pulse=92, temp=38.9, spo2=98, rr=18, height=160, weight=53, bmi=20.7),
            labs=[
                ("Serology", "2023-05-18", {"Widal Test": ("Positive (1:320)", "A")}),
            ],
            meds=[("Azithromycin", "18631", "500 mg", "once daily", "oral", "7 days")],
        ),
    ],
    "2345678905": [  # Bikash — CKD + hypertension + heart failure + anemia
        dict(
            department="Nephrology & Kidney Transplantation", doctor="Dr. Sabina Rana",
            date="2022-04-12", type="OPD", reason="Swelling of legs, fatigue",
            conditions=[("Chronic Kidney Disease, Stage 3", "N18.3", "2021-10-01"),
                        ("Essential Hypertension", "I10", "2018-01-01"),
                        ("Anemia of Chronic Disease", "D64.9", "2022-04-12")],
            vitals=dict(sbp=162, dbp=96, pulse=76, temp=36.5, spo2=96, rr=18, height=166, weight=70, bmi=25.4),
            labs=[
                ("Renal Function Test", "2022-04-12", {"Serum Creatinine": ("2.1", "H"), "Blood Urea": ("68", "H"), "eGFR": ("38", "L"), "Uric Acid": ("8.2", "H")}),
                ("Renal Function Test", "2023-04-20", {"Serum Creatinine": ("2.6", "H"), "Blood Urea": ("82", "H"), "eGFR": ("30", "L")}),
                ("Renal Function Test", "2024-05-15", {"Serum Creatinine": ("3.1", "H"), "Blood Urea": ("96", "H"), "eGFR": ("24", "L")}),
                ("Electrolytes", "2024-05-15", {"Potassium": ("5.6", "H"), "Sodium": ("136", "N"), "Chloride": ("104", "N")}),
                ("Complete Blood Count", "2024-05-15", {"Hemoglobin": ("9.4", "L"), "Hematocrit": ("29", "L")}),
            ],
            meds=[("Losartan", "52175", "50 mg", "once daily", "oral", "ongoing"),
                  ("Furosemide", "4603", "40 mg", "twice daily", "oral", "ongoing"),
                  ("Erythropoietin", "105694", "4000 IU", "weekly", "subcutaneous", "ongoing"),
                  ("Calcium Carbonate", "1897", "500 mg", "three times daily", "oral", "ongoing")],
        ),
        dict(
            department="Cardiology", doctor="Dr. Rajesh Malla",
            date="2023-12-01", type="OPD", reason="Breathlessness on exertion",
            conditions=[("Heart Failure", "I50.9", "2023-12-01")],
            vitals=dict(sbp=150, dbp=92, pulse=88, temp=36.6, spo2=94, rr=20, height=166, weight=72, bmi=26.1),
            labs=[
                ("Cardiac Markers", "2023-12-01", {"CRP": ("6.2", "H"), "Troponin I": ("0.03", "N")}),
            ],
            meds=[("Spironolactone", "9997", "25 mg", "once daily", "oral", "ongoing")],
        ),
        dict(
            department="Internal Medicine & Endocrinology", doctor="Dr. Anil Karki",
            date="2024-02-10", type="OPD", reason="Burning micturition",
            conditions=[("Urinary Tract Infection", "N39.0", "2024-02-10")],
            vitals=dict(sbp=148, dbp=90, pulse=80, temp=37.6, spo2=97, rr=18, height=166, weight=71, bmi=25.8),
            labs=[
                ("Urine Routine", "2024-02-10", {"Urine Pus Cells": ("40", "H"), "Urine Protein": ("+", "A")}),
            ],
            meds=[("Nitrofurantoin", "7454", "100 mg", "twice daily", "oral", "7 days")],
        ),
    ],
    "2345678906": [  # Maya — hepatology (Hep B, cirrhosis) + diabetes + PUD + TB
        dict(
            department="Gastroenterology, Hepatology and Endoscopy", doctor="Dr. Suresh Basnet",
            date="2021-07-14", type="OPD", reason="Jaundice, abdominal distension",
            conditions=[("Hepatitis B", "B18.1", "2019-01-01"),
                        ("Chronic Liver Disease / Cirrhosis", "K74.6", "2021-07-14"),
                        ("Type 2 Diabetes Mellitus", "E11.9", "2020-03-01")],
            vitals=dict(sbp=122, dbp=78, pulse=84, temp=36.7, spo2=97, rr=17, height=156, weight=58, bmi=23.8),
            labs=[
                ("Liver Function Test", "2021-07-14", {"SGPT (ALT)": ("128", "H"), "SGOT (AST)": ("142", "H"), "Total Bilirubin": ("3.4", "H"), "Serum Albumin": ("2.8", "L")}),
                ("Liver Function Test", "2022-09-10", {"SGPT (ALT)": ("96", "H"), "SGOT (AST)": ("110", "H"), "Total Bilirubin": ("2.6", "H"), "Serum Albumin": ("3.0", "L")}),
                ("Liver Function Test", "2024-01-08", {"SGPT (ALT)": ("74", "H"), "SGOT (AST)": ("82", "H"), "Total Bilirubin": ("2.1", "H"), "Serum Albumin": ("3.2", "L")}),
                ("Serology", "2021-07-14", {"HBsAg": ("Positive", "A")}),
                ("Coagulation Profile", "2021-07-14", {"Prothrombin Time": ("18.2", "H"), "INR": ("1.6", "H")}),
                ("Blood Sugar", "2021-07-14", {"Fasting Blood Glucose": ("156", "H"), "HbA1c": ("7.2", "H")}),
            ],
            meds=[("Tenofovir", "10184", "300 mg", "once daily", "oral", "ongoing"),
                  ("Propranolol", "8787", "20 mg", "twice daily", "oral", "ongoing"),
                  ("Metformin", "6809", "500 mg", "once daily", "oral", "ongoing")],
        ),
        dict(
            department="Gastroenterology, Hepatology and Endoscopy", doctor="Dr. Suresh Basnet",
            date="2023-03-20", type="OPD", reason="Epigastric pain",
            conditions=[("Peptic Ulcer Disease", "K27.9", "2023-03-20")],
            vitals=dict(sbp=118, dbp=76, pulse=80, temp=36.6, spo2=98, rr=16, height=156, weight=57, bmi=23.4),
            labs=[],
            meds=[("Pantoprazole", "40790", "40 mg", "once daily before breakfast", "oral", "8 weeks")],
        ),
        dict(
            department="Pulmonary, Critical Care & Sleep Medicine", doctor="Dr. Prakash Thapa",
            date="2022-02-15", type="OPD", reason="Chronic cough, weight loss, night sweats",
            conditions=[("Pulmonary Tuberculosis", "A15.0", "2022-02-15"),
                        ("Community Acquired Pneumonia", "J18.9", "2022-02-15")],
            vitals=dict(sbp=116, dbp=74, pulse=92, temp=38.2, spo2=94, rr=22, height=156, weight=54, bmi=22.2),
            labs=[
                ("Complete Blood Count", "2022-02-15", {"Total WBC Count": ("13.5", "H"), "Hemoglobin": ("11.2", "L")}),
            ],
            meds=[("Anti-TB Fixed Dose Combination (HRZE)", "", "4 tablets", "once daily", "oral", "6 months")],
        ),
    ],
    "2345678909": [  # Laxmi — young nurse: asthma + rhinitis -> subclinical hypothyroid
        dict(
            department="Pulmonology & Allergy Clinic", doctor="Dr. Prakash Thapa",
            date="2024-03-18", type="OPD", reason="Recurrent wheeze, allergic rhinitis",
            conditions=[("Bronchial Asthma", "J45.9", "2022-07-01"),
                        ("Allergic Rhinitis", "J30.9", "2022-07-01")],
            vitals=dict(sbp=112, dbp=74, pulse=70, temp=36.6, spo2=98, rr=17, height=160, weight=56, bmi=21.9),
            labs=[
                ("Complete Blood Count", "2024-03-18", {"Hemoglobin": ("13.1", "N"), "Total WBC Count": ("9.8", "N"), "Platelet Count": ("285", "N"), "Hematocrit": ("41", "N")}),
            ],
            meds=[("Budesonide Inhaler", "1808", "200 mcg", "twice daily", "inhalation", "ongoing"),
                  ("Salbutamol Inhaler", "435", "100 mcg", "2 puffs as needed", "inhalation", "ongoing")],
        ),
        dict(
            department="Internal Medicine & Endocrinology", doctor="Dr. Anil Karki",
            date="2024-09-05", type="OPD", reason="Fatigue, dry skin",
            conditions=[("Subclinical Hypothyroidism", "E03.9", "2024-09-05")],
            vitals=dict(sbp=116, dbp=76, pulse=62, temp=36.4, spo2=99, rr=15, height=160, weight=57, bmi=22.3),
            labs=[
                ("Thyroid Function Test", "2024-09-05", {"TSH": ("6.9", "H"), "Free T4": ("0.9", "N"), "Free T3": ("2.7", "N")}),
            ],
            meds=[("Levothyroxine", "10582", "50 mcg", "once daily before breakfast", "oral", "ongoing")],
        ),
    ],
    "2345678910": [  # Kiran — newly-diagnosed diabetes + HTN -> metabolic emergency
        dict(
            department="Internal Medicine & Endocrinology", doctor="Dr. Anil Karki",
            date="2023-06-08", type="OPD", reason="Newly diagnosed type 2 diabetes",
            conditions=[("Type 2 Diabetes Mellitus", "E11.9", "2023-06-08"),
                        ("Essential Hypertension", "I10", "2023-06-08"),
                        ("Obesity", "E66.9", "2021-01-15")],
            vitals=dict(sbp=148, dbp=94, pulse=86, temp=36.6, spo2=97, rr=17, height=176, weight=98, bmi=31.6),
            labs=[
                ("Blood Sugar", "2023-06-08", {"Fasting Blood Glucose": ("168", "H"), "HbA1c": ("8.2", "H"), "Postprandial Glucose": ("238", "H")}),
                ("Lipid Profile", "2023-06-08", {"Total Cholesterol": ("242", "H"), "LDL Cholesterol": ("164", "H"), "HDL Cholesterol": ("36", "L"), "Triglycerides": ("228", "H")}),
            ],
            meds=[("Metformin", "6809", "500 mg", "twice daily", "oral", "ongoing"),
                  ("Losartan", "52175", "25 mg", "once daily", "oral", "ongoing")],
        ),
        dict(
            department="Emergency Medicine And Pre-Hospital Care", doctor="Dr. Nabin Adhikari",
            date="2024-07-02", type="Emergency", reason="Severe abdominal pain, vomiting, palpitations",
            conditions=[("Acute Gastroenteritis", "A09", "2024-07-02"),
                        ("Hypokalemia", "E87.6", "2024-07-02")],
            vitals=dict(sbp=158, dbp=96, pulse=112, temp=37.9, spo2=96, rr=20, height=176, weight=97, bmi=31.3),
            labs=[
                ("Electrolytes", "2024-07-02", {"Sodium": ("140", "N"), "Potassium": ("3.2", "L"), "Chloride": ("106", "N")}),
                ("Complete Blood Count", "2024-07-02", {"Total WBC Count": ("12.8", "H"), "Hemoglobin": ("15.4", "N")}),
            ],
            meds=[("Paracetamol", "161", "500 mg", "every 6 hours as needed", "oral", "5 days"),
                  ("Metronidazole", "8621", "400 mg", "three times daily", "oral", "7 days")],
        ),
    ],
}


class Command(BaseCommand):
    help = "Rich, idempotent seed for Nepal Mediciti Hospital."

    def handle(self, *args, **options):
        n_cond = n_vit = n_lab = n_res = n_med = n_alg = 0
        for nid, demo in PATIENTS.items():
            patient = self._patient(nid, demo)
            meta = {"nid": nid, "full_name": demo["name"], "date_of_birth": demo["dob"],
                    "gender": demo["gender"], "phone": demo["phone"]}
            n_alg += self._allergies(patient, demo)

            for ep in JOURNEYS.get(nid, []):
                enc = self._encounter(patient, ep)
                for text, icd, onset in ep.get("conditions", []):
                    cond = self._condition(patient, enc, text, icd, onset)
                    n_cond += 1
                    services.push_index(nid, meta, "Condition", cond.id, onset, f"{text} ({icd})")
                if ep.get("vitals"):
                    self._vitals(patient, enc, ep["vitals"])
                    n_vit += 1
                for panel, date, overrides in ep.get("labs", []):
                    report, results = self._lab(patient, enc, panel, date, overrides, ep["doctor"])
                    n_lab += 1
                    n_res += len(results)
                    services.push_index(nid, meta, "DiagnosticReport", report.id, date, f"{panel} report")
                    for res in results:
                        services.push_index(nid, meta, "Observation", f"labresult-{res.id}", date,
                                            f"{res.test_name}: {res.value} {res.unit}".strip())
                for name, rx, dose, freq, route, dur in ep.get("meds", []):
                    med = self._medication(patient, enc, name, rx, dose, freq, route, dur, ep["date"], ep["doctor"])
                    n_med += 1
                    services.push_index(nid, meta, "MedicationRequest", med.id, ep["date"], f"{name} {dose} {freq}")

        self.stdout.write(self.style.SUCCESS(
            f"Mediciti seeded: {len(PATIENTS)} patients, {n_cond} conditions, {n_vit} vitals sets, "
            f"{n_lab} lab reports, {n_res} lab results, {n_med} medications, {n_alg} allergies."))

    # -- idempotent writers -------------------------------------------------
    def _patient(self, nid, demo):
        defaults = dict(
            full_name=demo["name"], dob=demo["dob"], gender=demo["gender"], phone=demo["phone"],
            mrn=f"MED-{nid[-4:]}", address=demo["address"], blood_group=demo["blood_group"],
            marital_status=demo["marital"], occupation=demo["occupation"], ethnicity=demo["ethnicity"],
            emergency_contact_name=demo["ec_name"], emergency_contact_phone=demo["ec_phone"],
        )
        p, created = LocalPatient.objects.get_or_create(nid=nid, defaults=defaults)
        if not created:
            for k, v in defaults.items():
                setattr(p, k, v)
            p.save()
        return p

    def _allergies(self, patient, demo):
        count = 0
        for allergen, reaction, severity, date in demo.get("allergies", []):
            _, created = Allergy.objects.get_or_create(
                patient=patient, allergen=allergen,
                defaults={"reaction": reaction, "severity": severity, "recorded_date": date})
            count += 1 if created else 0
        return count

    def _encounter(self, patient, ep):
        enc, _ = Encounter.objects.get_or_create(
            patient=patient, department=ep["department"], encounter_date=ep["date"],
            defaults={"doctor_name": ep["doctor"], "encounter_type": ep["type"], "reason": ep["reason"]})
        return enc

    def _condition(self, patient, enc, text, icd, onset):
        obj, _ = Condition.objects.get_or_create(
            patient=patient, diagnosis_text=text, onset_date=onset,
            defaults={"encounter": enc, "icd10_code": icd, "clinical_status": "active", "recorded_date": onset})
        return obj

    def _vitals(self, patient, enc, v):
        obj, _ = Vitals.objects.get_or_create(
            patient=patient, encounter=enc,
            defaults=dict(systolic_bp=v.get("sbp"), diastolic_bp=v.get("dbp"), pulse=v.get("pulse"),
                          temperature=v.get("temp"), spo2=v.get("spo2"), respiratory_rate=v.get("rr"),
                          height_cm=v.get("height"), weight_kg=v.get("weight"), bmi=v.get("bmi")))
        return obj

    def _lab(self, patient, enc, panel, date, overrides, doctor):
        tests = PANELS.get(panel, [])
        report = LabReport.objects.filter(patient=patient, panel_name=panel, report_date=date).first()
        if report is None:
            order = LabOrder.objects.create(
                patient=patient, encounter=enc, panel_name=panel,
                ordering_doctor=doctor, priority="routine")
            report = LabReport.objects.create(
                order=order, patient=patient, panel_name=panel, report_date=date, status="final")
        results = []
        for name, loinc, unit, ref, normal in tests:
            if overrides is not None and name in overrides:
                value, interp = overrides[name]
            else:
                value, interp = normal, "N"
            res, _ = LabResult.objects.get_or_create(
                report=report, test_name=name,
                defaults={"patient": patient, "loinc_code": loinc, "value": value,
                          "unit": unit, "reference_range": ref, "interpretation": interp})
            results.append(res)
        return report, results

    def _medication(self, patient, enc, name, rx, dose, freq, route, dur, date, prescriber):
        obj, _ = MedicationRequest.objects.get_or_create(
            patient=patient, medication_name=name, prescribed_date=date,
            defaults={"encounter": enc, "rxnorm_code": rx, "dosage": dose, "frequency": freq,
                      "route": route, "duration": dur, "prescriber": prescriber})
        return obj
