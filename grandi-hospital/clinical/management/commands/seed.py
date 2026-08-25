"""
Rich, realistic seed for Grandi Hospital ("variant B" schema).

Grandi is modeled as a NEUROSCIENCE & MATERNAL-CARE centre — deliberately a
different speciality mix from Norvic (cardiac) so every facility contributes
a distinct clinical voice to the federation. It shares nine patients with the
other facilities (NIDs ...901, ...902, ...903, ...909, ...910, ...915, ...920,
...921, ...927). For those, demographics are CANONICAL (identical to Mediciti,
Norvic and both labs) but every encounter, condition, lab, medication and
vaccine recorded HERE is unique to Grandi. It also has its own EXCLUSIVE
patients (...931, ...932, ...933, ...934) seen nowhere else in the federation.

Like Norvic it contributes Immunization + Procedure resources on top of the
shared clinical model.

Every writer is IDEMPOTENT (get_or_create on natural keys) so re-running never
duplicates rows. Safe to run repeatedly.

Run:  python manage.py seed
"""
from django.core.management.base import BaseCommand

from clinical import services
from clinical.models import (
    Allergy,
    Condition,
    Encounter,
    Immunization,
    LabOrder,
    LabReport,
    LabResult,
    LocalPatient,
    MedicationRequest,
    Procedure,
    Vitals,
)

# Lab panel catalogue: panel -> list of (test, LOINC, unit, ref_range, normal)
# Grandi runs a neuro / endocrine / maternal-oriented menu.
PANELS = {
    "Complete Blood Count": [
        ("Hemoglobin", "718-7", "g/dL", "13.0-17.0", "14.5"),
        ("Total WBC Count", "6690-2", "10^3/uL", "4.0-11.0", "7.2"),
        ("Platelet Count", "777-3", "10^3/uL", "150-400", "250"),
        ("Hematocrit", "4544-3", "%", "40-50", "44"),
    ],
    "Thyroid Profile": [
        ("TSH", "3016-8", "mIU/L", "0.4-4.0", "2.1"),
        ("Free T4", "3024-7", "ng/dL", "0.8-1.8", "1.2"),
    ],
    "Blood Sugar": [
        ("Fasting Blood Glucose", "1558-6", "mg/dL", "70-100", "92"),
        ("HbA1c", "4548-4", "%", "4.0-5.6", "5.3"),
    ],
    "Coagulation Profile": [
        ("Prothrombin Time", "5902-2", "sec", "11-13.5", "12.0"),
        ("INR", "6301-6", "", "0.8-1.1", "1.0"),
        ("APTT", "3173-2", "sec", "25-35", "30"),
    ],
    "Electrolytes": [
        ("Sodium", "2951-2", "mmol/L", "135-145", "140"),
        ("Potassium", "2823-3", "mmol/L", "3.5-5.1", "4.2"),
        ("Chloride", "2075-0", "mmol/L", "98-107", "102"),
    ],
    "Renal Function Test": [
        ("Blood Urea", "3094-0", "mg/dL", "15-40", "28"),
        ("Serum Creatinine", "2160-0", "mg/dL", "0.7-1.3", "1.0"),
        ("eGFR", "33914-3", "mL/min", ">90", "95"),
    ],
    "Liver Function Test": [
        ("ALT (SGPT)", "1742-6", "U/L", "<41", "26"),
        ("AST (SGOT)", "1920-8", "U/L", "<40", "24"),
        ("Total Bilirubin", "1975-2", "mg/dL", "0.1-1.2", "0.7"),
        ("Alkaline Phosphatase", "6768-6", "U/L", "38-126", "84"),
    ],
}

# Canonical demographics. NIDs shared with other facilities MUST match their
# seeds exactly (name / dob / gender / phone) so the National Platform links
# them to one citizen; see tools/check_seed_consistency.py. first/last split
# for variant B.
PATIENTS = {
    "2345678901": dict(
        first="Ram Bahadur", last="Thapa", dob="1970-05-12", gender="MALE", phone="9841000001",
        address="Kupondole, Lalitpur", blood_group="O+", marital="Married",
        occupation="Retired Teacher", ethnicity="Chhetri",
        ec_name="Sita Thapa", ec_phone="9800000011",
        allergies=[("Aspirin", "Gastric upset", "mild", "2022-01-15")],
    ),
    "2345678902": dict(
        first="Sita Kumari", last="Sharma", dob="1988-11-23", gender="FEMALE", phone="9803000002",
        address="Baneshwor, Kathmandu", blood_group="A+", marital="Married",
        occupation="Bank Officer", ethnicity="Brahmin",
        ec_name="Gopal Sharma", ec_phone="9800000022",
        allergies=[],
    ),
    "2345678903": dict(
        first="Hari Prasad", last="Koirala", dob="1979-02-03", gender="MALE", phone="9841000003",
        address="Biratnagar, Morang", blood_group="B+", marital="Married",
        occupation="Businessman", ethnicity="Brahmin",
        ec_name="Radha Koirala", ec_phone="9800000033",
        allergies=[("Sulfonamides", "Urticaria", "severe", "2018-09-01")],
    ),
    # --- Cross-facility demo patients (NIDs ...09/.10 match Mediciti + both labs) ---
    "2345678909": dict(
        first="Laxmi Maya", last="Tamang", dob="1993-04-14", gender="FEMALE", phone="9842000001",
        address="Jhamsikhel, Lalitpur", blood_group="O+", marital="Single",
        occupation="Registered Nurse", ethnicity="Tamang",
        ec_name="Sunita Tamang", ec_phone="9800000099",
        allergies=[],
    ),
    "2345678910": dict(
        first="Kiran Bahadur", last="Limbu", dob="1985-09-19", gender="MALE", phone="9842000002",
        address="Sundhara, Kathmandu", blood_group="A+", marital="Married",
        occupation="IT Manager", ethnicity="Limbu",
        ec_name="Roshni Limbu", ec_phone="9800000100",
        allergies=[],
    ),
    # --- Expanded federation cohort. Demographics are CANONICAL: name/dob/gender/
    # phone MUST match Mediciti + both labs. ---
    "2345678915": dict(
        first="Prakash Bahadur", last="Magar", dob="1963-11-27", gender="MALE", phone="9841000015",
        address="Tansen, Palpa", blood_group="O+", marital="Married",
        occupation="Retired Police", ethnicity="Magar",
        ec_name="Dil Kumari Magar", ec_phone="9800000115",
        allergies=[],
    ),
    "2345678920": dict(
        first="Anita Rai", last="Subba", dob="1998-02-25", gender="FEMALE", phone="9841000020",
        address="Itahari, Sunsari", blood_group="A+", marital="Single",
        occupation="Hotel Receptionist", ethnicity="Rai",
        ec_name="Bhim Rai", ec_phone="9800000120",
        allergies=[("Penicillin", "Angioedema", "severe", "2017-11-02")],
    ),
    "2345678921": dict(
        first="Gopal Krishna", last="Neupane", dob="1960-04-16", gender="MALE", phone="9841000021",
        address="Gorkha Bazar, Gorkha", blood_group="B+", marital="Married",
        occupation="Retired Farmer", ethnicity="Brahmin",
        ec_name="Tulasa Neupane", ec_phone="9800000121",
        allergies=[],
    ),
    "2345678927": dict(
        first="Krishna Bahadur", last="Khadka", dob="1966-12-01", gender="MALE", phone="9841000027",
        address="Kalanki, Kathmandu", blood_group="O+", marital="Married",
        occupation="Bus Driver", ethnicity="Chhetri",
        ec_name="Nirmala Khadka", ec_phone="9800000127",
        allergies=[],
    ),
    # --- GRANDI-EXCLUSIVE patients (seen at no other facility in the demo) ---
    "2345678931": dict(
        first="Sunita", last="Shrestha", dob="1994-03-22", gender="FEMALE", phone="9851200031",
        address="Jhapel, Lalitpur", blood_group="AB+", marital="Married",
        occupation="Housewife", ethnicity="Newar",
        ec_name="Bikash Shrestha", ec_phone="9800000131",
        allergies=[],
    ),
    "2345678932": dict(
        first="Bikash", last="Gurung", dob="1987-11-08", gender="MALE", phone="9851200032",
        address="Lakeside, Kaski", blood_group="O-", marital="Single",
        occupation="Trekking Guide", ethnicity="Gurung",
        ec_name="Mina Gurung", ec_phone="9800000132",
        allergies=[("Metronidazole", "Metallic taste, nausea", "mild", "2021-05-20")],
    ),
    "2345678933": dict(
        first="Sabina", last="Chaudhary", dob="1996-07-30", gender="FEMALE", phone="9851200033",
        address="Adarsh Nagar, Birgunj", blood_group="B+", marital="Single",
        occupation="University Student", ethnicity="Tharu",
        ec_name="Ram Chaudhary", ec_phone="9800000133",
        allergies=[],
    ),
    "2345678934": dict(
        first="Dinesh", last="Yadav", dob="1959-01-17", gender="MALE", phone="9851200034",
        address="Ward 5, Janakpurdham", blood_group="A+", marital="Married",
        occupation="Shopkeeper", ethnicity="Yadav",
        ec_name="Kamla Yadav", ec_phone="9800000134",
        allergies=[],
    ),
}

# Clinical journeys (variant-B fields are filled by the writers below).
JOURNEYS = {
    "2345678901": [  # Ram — also at Mediciti & Norvic; here Grande's neurology clinic
        dict(
            department="Neurology", physician="Dr. Pramila Shrestha",
            date="2024-07-18", category="OPD", complaint="Recurrent throbbing headaches with neck stiffness",
            conditions=[("Cervical Spondylosis", "M47.2", "2024-07-18"),
                        ("Essential Hypertension", "I10", "2018-03-10")],
            vitals=dict(sbp=146, dbp=92, pulse=78, temp=36.5, spo2=98, rr=16, height=168, weight=74, bmi=26.2),
            labs=[
                ("Complete Blood Count", "2024-07-18", {"Hemoglobin": ("14.1", "N"), "Total WBC Count": ("7.8", "N")}),
                ("Electrolytes", "2024-07-18", {"Sodium": ("139", "N"), "Potassium": ("4.1", "N")}),
            ],
            meds=[("Amitriptyline", "704", "25 mg", "once daily at night", "oral", "ongoing"),
                  ("Aceclofenac", "32967", "100 mg", "twice daily after food", "oral", "2 weeks")],
        ),
    ],
    "2345678902": [  # Sita — identity shared everywhere; her thyroid work-up lives at Grandi
        dict(
            department="Endocrinology & Diabetes", physician="Dr. Bijay Rauniyar",
            date="2024-10-03", category="OPD", complaint="Weight gain, cold intolerance, fatigue",
            conditions=[("Hypothyroidism", "E03.9", "2024-10-03"),
                        ("Vitamin D Deficiency", "E55.9", "2024-10-03")],
            vitals=dict(sbp=118, dbp=76, pulse=68, temp=36.3, spo2=99, rr=14, height=158, weight=71, bmi=28.4),
            labs=[
                ("Thyroid Profile", "2024-10-03", {"TSH": ("8.9", "H"), "Free T4": ("0.7", "L")}),
                ("Complete Blood Count", "2024-10-03", {"Hemoglobin": ("12.2", "L"), "Platelet Count": ("265", "N")}),
            ],
            meds=[("Levothyroxine", "103588", "50 mcg", "once daily before breakfast", "oral", "ongoing"),
                  ("Cholecalciferol", "11248", "60000 IU", "once weekly", "oral", "8 weeks")],
        ),
    ],
    "2345678903": [  # Hari — cardiac care was at Norvic; his new-onset epilepsy is a Grandi case
        dict(
            department="Neurology", physician="Dr. Pramila Shrestha",
            date="2024-05-02", category="Inpatient", complaint="Two episodes of generalized tonic-clonic seizures",
            conditions=[("Epilepsy", "G40.9", "2024-05-02")],
            vitals=dict(sbp=132, dbp=86, pulse=92, temp=36.9, spo2=96, rr=18, height=172, weight=80, bmi=27.0),
            labs=[
                ("Electrolytes", "2024-05-02", {"Sodium": ("136", "N"), "Potassium": ("3.9", "N")}),
                ("Complete Blood Count", "2024-05-02", {"Total WBC Count": ("11.4", "H"), "Hemoglobin": ("14.6", "N")}),
                ("Blood Sugar", "2024-05-02", {"Fasting Blood Glucose": ("104", "N"), "HbA1c": ("5.7", "N")}),
            ],
            meds=[("Levetiracetam", "834061", "500 mg", "twice daily", "oral", "ongoing"),
                  ("Lacosamide", "834060", "100 mg", "twice daily", "oral", "ongoing")],
            procedures=[
                ("Lumbar Puncture (diagnostic CSF study)",
                 "277786009", "Neurology Procedure", "2024-05-03", "Dr. Pramila Shrestha",
                 "Successful, normal opening pressure", "CSF analysis unremarkable; no evidence of infection."),
                ("Computerized Tomography of Head",
                 "241657007", "Imaging", "2024-05-02", "Dr. Pramila Shrestha",
                 "Completed", "Non-contrast CT head: no acute intracranial abnormality."),
            ],
        ),
        dict(
            department="Neurology", physician="Dr. Pramila Shrestha",
            date="2024-08-14", category="OPD", complaint="Seizure-free follow-up, drug level review",
            conditions=[],
            vitals=dict(sbp=128, dbp=82, pulse=76, temp=36.5, spo2=98, rr=16, height=172, weight=79, bmi=26.7),
            labs=[],
            meds=[],
        ),
    ],
    "2345678909": [  # Laxmi — also at Mediciti & Norvic; her antenatal care is at Grandi
        dict(
            department="Obstetrics & Gynecology", physician="Dr. Anjana Karki",
            date="2024-08-28", category="OPD", complaint="Routine antenatal check-up, 36 weeks",
            conditions=[("Full-Term Pregnancy", "Z37.0", "2024-08-28")],
            vitals=dict(sbp=112, dbp=70, pulse=84, temp=36.6, spo2=99, rr=16, height=160, weight=68, bmi=26.6),
            labs=[
                ("Complete Blood Count", "2024-08-28", {"Hemoglobin": ("11.2", "L"), "Platelet Count": ("255", "N")}),
                ("Blood Sugar", "2024-08-28", {"Fasting Blood Glucose": ("88", "N"), "HbA1c": ("5.0", "N")}),
            ],
            meds=[("Ferrous Sulphate", "310965", "200 mg", "twice daily", "oral", "ongoing"),
                  ("Folic Acid", "4511", "5 mg", "once daily", "oral", "ongoing")],
        ),
    ],
    "2345678910": [  # Kiran — chest pain assessed at Norvic & Mediciti; knee pain at Grandi
        dict(
            department="Orthopedics", physician="Dr. Suraj Joshi",
            date="2024-09-12", category="OPD", complaint="Right knee pain on stairs for six months",
            conditions=[("Osteoarthritis of Knee", "M17.0", "2024-09-12")],
            vitals=dict(sbp=138, dbp=88, pulse=80, temp=36.5, spo2=98, rr=16, height=176, weight=95, bmi=30.7),
            labs=[
                ("Renal Function Test", "2024-09-12", {"Serum Creatinine": ("0.9", "N"), "eGFR": ("97", "N")}),
            ],
            meds=[("Paracetamol", "161", "650 mg", "as needed up to 4x daily", "oral", "as needed"),
                  ("Diclofenac Gel", "32969", "1%", "apply twice daily", "topical", "4 weeks")],
        ),
    ],
    # --- Expanded cohort (NIDs ...15/...20/...21/...27) ---
    "2345678915": [  # Prakash — PCI was at Norvic; his parkinsonism work-up is at Grandi
        dict(
            department="Neurology", physician="Dr. Pramila Shrestha",
            date="2024-06-21", category="OPD", complaint="Resting tremor right hand, slowing of movement",
            conditions=[("Parkinson Disease", "G20", "2024-06-21")],
            vitals=dict(sbp=130, dbp=80, pulse=74, temp=36.4, spo2=97, rr=16, height=165, weight=69, bmi=25.3),
            labs=[
                ("Complete Blood Count", "2024-06-21", {"Hemoglobin": ("14.0", "N"), "Platelet Count": ("240", "N")}),
                ("Renal Function Test", "2024-06-21", {"Serum Creatinine": ("1.0", "N"), "Blood Urea": ("32", "N")}),
            ],
            meds=[("Levodopa/Carbidopa", "32443", "100/25 mg", "three times daily", "oral", "ongoing"),
                  ("Pramipexole", "1191", "0.25 mg", "three times daily", "oral", "ongoing")],
        ),
    ],
    "2345678920": [  # Anita — asthma reviewed at Mediciti & Norvic; rhinitis plan at Grandi
        dict(
            department="General Medicine & Pulmonology", physician="Dr. Rajan Adhikari",
            date="2024-07-05", category="OPD", complaint="Seasonal sneezing and wheeze worsening in spring",
            conditions=[("Allergic Rhinitis", "J30.4", "2024-07-05"),
                        ("Bronchial Asthma", "J45.9", "2019-05-01")],
            vitals=dict(sbp=108, dbp=70, pulse=76, temp=36.5, spo2=99, rr=17, height=158, weight=52, bmi=20.8),
            labs=[
                ("Complete Blood Count", "2024-07-05", {"Total WBC Count": ("8.2", "N"), "Hemoglobin": ("12.8", "L")}),
            ],
            meds=[("Montelukast", "33049", "10 mg", "once daily at night", "oral", "ongoing"),
                  ("Cetirizine", "83288", "10 mg", "as needed at night", "oral", "as needed")],
        ),
    ],
    "2345678921": [  # Gopal — cor pulmonale assessed at Norvic; his stroke admission is Grandi's
        dict(
            department="Neurology (Stroke Unit)", physician="Dr. Pramila Shrestha",
            date="2024-04-19", category="Inpatient", complaint="Sudden left-sided weakness and slurred speech, onset 3 hours ago",
            conditions=[("Acute Ischemic Stroke", "I63.9", "2024-04-19"),
                        ("Atrial Fibrillation", "I48.0", "2024-04-19")],
            vitals=dict(sbp=158, dbp=94, pulse=104, temp=36.8, spo2=93, rr=20, height=163, weight=56, bmi=21.1),
            labs=[
                ("Coagulation Profile", "2024-04-19", {"INR": ("1.0", "N"), "APTT": ("29", "N")}),
                ("Complete Blood Count", "2024-04-19", {"Total WBC Count": ("9.6", "N"), "Platelet Count": ("228", "N")}),
                ("Blood Sugar", "2024-04-19", {"Fasting Blood Glucose": ("156", "H"), "HbA1c": ("6.8", "H")}),
            ],
            meds=[("Clopidogrel", "32968", "75 mg", "once daily", "oral", "ongoing"),
                  ("Rosuvastatin", "314452", "20 mg", "once daily at night", "oral", "ongoing")],
            procedures=[
                ("Computerized Tomography of Head",
                 "241657007", "Imaging", "2024-04-19", "Dr. Pramila Shrestha",
                 "Completed", "NCCT head: hypodensity in right MCA territory; no hemorrhage — within thrombolysis window."),
            ],
        ),
        dict(
            department="Neurology (Stroke Unit)", physician="Dr. Pramila Shrestha",
            date="2024-05-24", category="OPD", complaint="Post-stroke follow-up, walking improved with support",
            conditions=[],
            vitals=dict(sbp=142, dbp=86, pulse=88, temp=36.5, spo2=95, rr=18, height=163, weight=57, bmi=21.4),
            labs=[
                ("Coagulation Profile", "2024-05-24", {"INR": ("1.0", "N"), "Prothrombin Time": ("12.1", "N")}),
            ],
            meds=[("Apixaban", "1243592", "5 mg", "twice daily", "oral", "ongoing")],
        ),
    ],
    "2345678927": [  # Krishna — cardiac work-up elsewhere; insulin intensification at Grandi
        dict(
            department="Endocrinology & Diabetes", physician="Dr. Bijay Rauniyar",
            date="2024-05-08", category="OPD", complaint="Uncontrolled sugars despite maximum oral agents, burning feet",
            conditions=[("Type 2 Diabetes Mellitus", "E11.9", "2014-03-01"),
                        ("Diabetic Peripheral Neuropathy", "E11.4", "2024-05-08")],
            vitals=dict(sbp=148, dbp=90, pulse=84, temp=36.6, spo2=97, rr=17, height=169, weight=84, bmi=29.4),
            labs=[
                ("Blood Sugar", "2024-05-08", {"Fasting Blood Glucose": ("189", "H"), "HbA1c": ("9.1", "H")}),
                ("Renal Function Test", "2024-05-08", {"Serum Creatinine": ("1.1", "N"), "eGFR": ("82", "N")}),
                ("Liver Function Test", "2024-05-08", {"ALT (SGPT)": ("42", "H"), "AST (SGOT)": ("38", "N")}),
            ],
            meds=[("Insulin Glargine", "274755", "18 units", "once daily at bedtime", "subcutaneous", "ongoing"),
                  ("Metformin", "6809", "1000 mg", "twice daily with meals", "oral", "ongoing"),
                  ("Pregabalin", "189308", "75 mg", "twice daily", "oral", "ongoing")],
        ),
    ],
    # --- GRANDI-exclusive journeys ---
    "2345678931": [  # Sunita — delivered her first baby at Grandi
        dict(
            department="Obstetrics & Gynecology", physician="Dr. Anjana Karki",
            date="2024-09-30", category="Inpatient", complaint="Term pregnancy with spontaneous onset of labour",
            conditions=[("Live Birth, Full-Term", "Z37.0", "2024-09-30")],
            vitals=dict(sbp=118, dbp=74, pulse=90, temp=36.7, spo2=98, rr=18, height=157, weight=72, bmi=29.2),
            labs=[
                ("Complete Blood Count", "2024-09-30", {"Hemoglobin": ("11.8", "L"), "Platelet Count": ("270", "N")}),
                ("Coagulation Profile", "2024-09-30", {"INR": ("1.0", "N"), "APTT": ("31", "N")}),
            ],
            meds=[("Paracetamol", "161", "1 g", "as needed up to 4x daily", "oral", "5 days"),
                  ("Ferrous Sulphate", "310965", "200 mg", "twice daily", "oral", "3 months")],
            procedures=[
                ("Normal Vaginal Delivery",
                 "236974004", "Obstetric Procedure", "2024-09-30", "Dr. Anjana Karki",
                 "Successful, healthy baby girl 3.1 kg", "Spontaneous vaginal delivery at term; second-degree tear repaired."),
            ],
        ),
    ],
    "2345678932": [  # Bikash — trekking guide; appendicitis on return from Annapurna circuit
        dict(
            department="General Surgery", physician="Dr. Ashok Shrestha",
            date="2024-07-22", category="Inpatient", complaint="Two days of right lower abdominal pain, anorexia, fever",
            conditions=[("Acute Appendicitis", "K35.8", "2024-07-22")],
            vitals=dict(sbp=124, dbp=78, pulse=102, temp=38.2, spo2=98, rr=20, height=173, weight=66, bmi=22.1),
            labs=[
                ("Complete Blood Count", "2024-07-22", {"Total WBC Count": ("15.8", "H"), "Hemoglobin": ("14.9", "N")}),
                ("Coagulation Profile", "2024-07-22", {"INR": ("1.0", "N"), "Prothrombin Time": ("11.9", "N")}),
            ],
            meds=[("Ceftriaxone", "33131", "1 g", "twice daily", "intravenous", "5 days"),
                  ("Paracetamol", "161", "1 g", "three times daily", "intravenous", "3 days")],
            procedures=[
                ("Laparoscopic Appendicectomy",
                 "16326008", "General Surgery", "2024-07-22", "Dr. Ashok Shrestha",
                 "Successful, uneventful recovery", "Inflamed non-perforated appendix removed; discharged on day 3."),
            ],
        ),
    ],
    "2345678933": [  # Sabina — migraine clinic patient
        dict(
            department="Neurology", physician="Dr. Pramila Shrestha",
            date="2024-08-15", category="OPD", complaint="Unilateral pulsating headaches with photophobia, twice weekly",
            conditions=[("Migraine without Aura", "G43.0", "2024-08-15")],
            vitals=dict(sbp=106, dbp=68, pulse=72, temp=36.4, spo2=99, rr=15, height=161, weight=51, bmi=19.7),
            labs=[
                ("Complete Blood Count", "2024-08-15", {"Hemoglobin": ("12.6", "L"), "Total WBC Count": ("6.9", "N")}),
            ],
            meds=[("Sumatriptan", "21167", "50 mg", "at onset of attack, max once per attack", "oral", "as needed"),
                  ("Propranolol", "9342", "40 mg", "twice daily", "oral", "3 months")],
        ),
    ],
    "2345678934": [  # Dinesh — COPD exacerbation admission
        dict(
            department="General Medicine & Pulmonology", physician="Dr. Rajan Adhikari",
            date="2024-06-03", category="Inpatient", complaint="Increased breathlessness and purulent sputum for four days",
            conditions=[("Chronic Obstructive Pulmonary Disease with Acute Exacerbation", "J44.1", "2015-11-20")],
            vitals=dict(sbp=134, dbp=82, pulse=98, temp=37.1, spo2=87, rr=24, height=166, weight=58, bmi=21.1),
            labs=[
                ("Complete Blood Count", "2024-06-03", {"Total WBC Count": ("13.8", "H"), "Hematocrit": ("52", "H")}),
                ("Electrolytes", "2024-06-03", {"Sodium": ("134", "L"), "Potassium": ("4.4", "N"), "Chloride": ("99", "N")}),
            ],
            meds=[("Salbutamol Nebuliser Solution", "435", "5 mg", "every 6 hours as needed", "nebulisation", "during admission"),
                  ("Prednisolone", "834018", "40 mg", "once daily", "oral", "5 days"),
                  ("Doxycycline", "3640", "100 mg", "twice daily", "oral", "7 days")],
        ),
        dict(
            department="General Medicine & Pulmonology", physician="Dr. Rajan Adhikari",
            date="2024-07-10", category="OPD", complaint="COPD follow-up back to baseline, smoking cessation advice",
            conditions=[],
            vitals=dict(sbp=128, dbp=78, pulse=84, temp=36.5, spo2=92, rr=19, height=166, weight=58, bmi=21.1),
            labs=[],
            meds=[("Tiotropium Inhaler", "895456", "18 mcg", "one puff once daily", "inhalation", "ongoing")],
        ),
    ],
}

# Immunizations per patient: (vaccine, cvx, dose, lot, site, route, date, by)
IMMUNIZATIONS = {
    "2345678901": [
        ("Influenza, seasonal", "141", "Annual", "GRN-FLU24-07", "Left deltoid", "Intramuscular", "2024-07-18", "Nurse Kamala Rai"),
    ],
    "2345678903": [
        ("Hepatitis B (adult)", "45", "1", "GRN-HBV24-12", "Left deltoid", "Intramuscular", "2024-08-14", "Nurse Bishnu Ale"),
    ],
    "2345678909": [
        ("Tdap (Tetanus-diphtheria-acellular pertussis)", "115", "Booster", "GRN-TDA24-21", "Left deltoid", "Intramuscular", "2024-08-28", "Nurse Bishnu Ale"),
    ],
    "2345678920": [
        ("Influenza, seasonal", "141", "Annual", "GRN-FLU24-19", "Right deltoid", "Intramuscular", "2024-07-05", "Nurse Kamala Rai"),
    ],
    "2345678921": [
        ("Pneumococcal (PCV13)", "133", "1", "GRN-PCV24-04", "Left deltoid", "Intramuscular", "2024-05-24", "Nurse Kamala Rai"),
        ("Influenza, seasonal", "141", "Annual", "GRN-FLU24-23", "Right deltoid", "Intramuscular", "2024-05-24", "Nurse Kamala Rai"),
    ],
    "2345678927": [
        ("Influenza, seasonal", "141", "Annual", "GRN-FLU24-31", "Left deltoid", "Intramuscular", "2024-05-08", "Nurse Bishnu Ale"),
    ],
    # --- Grandi exclusives ---
    "2345678933": [
        ("HPV (human papillomavirus, 9-valent)", "186", "1", "GRN-HPV24-02", "Left deltoid", "Intramuscular", "2024-08-15", "Nurse Bishnu Ale"),
    ],
    "2345678934": [
        ("Pneumococcal (PCV13)", "133", "1", "GRN-PCV24-09", "Left deltoid", "Intramuscular", "2024-07-10", "Nurse Kamala Rai"),
        ("Influenza, seasonal", "141", "Annual", "GRN-FLU24-44", "Right deltoid", "Intramuscular", "2024-07-10", "Nurse Kamala Rai"),
    ],
}


class Command(BaseCommand):
    help = "Rich, idempotent seed for Grandi Hospital."

    def handle(self, *args, **options):
        n_cond = n_vit = n_lab = n_res = n_med = n_alg = n_imm = n_proc = 0
        for nid, demo in PATIENTS.items():
            patient = self._patient(nid, demo)
            meta = {"nid": nid, "full_name": f"{demo['first']} {demo['last']}".strip(),
                    "date_of_birth": demo["dob"], "gender": demo["gender"], "phone": demo["phone"]}
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
                    report, results = self._lab(patient, enc, panel, date, overrides, ep["physician"])
                    n_lab += 1
                    n_res += len(results)
                    services.push_index(nid, meta, "DiagnosticReport", report.id, date, f"{panel} report")
                    for res in results:
                        services.push_index(nid, meta, "Observation", f"labresult-{res.id}", date,
                                            f"{res.test_name}: {res.value} {res.unit}".strip())
                for name, rx, dose, freq, route, dur in ep.get("meds", []):
                    med = self._medication(patient, enc, name, rx, dose, freq, route, dur, ep["date"], ep["physician"])
                    n_med += 1
                    services.push_index(nid, meta, "MedicationRequest", med.id, ep["date"], f"{name} {dose} {freq}")
                for pname, snomed, cat, pdate, surgeon, outcome, notes in ep.get("procedures", []):
                    proc = self._procedure(patient, enc, pname, snomed, cat, pdate, surgeon, outcome, notes)
                    n_proc += 1
                    services.push_index(nid, meta, "Procedure", proc.id, pdate, f"{pname} ({outcome})")

            for vaccine, cvx, dose, lot, site, route, date, by in IMMUNIZATIONS.get(nid, []):
                imm = self._immunization(patient, vaccine, cvx, dose, lot, site, route, date, by)
                n_imm += 1
                services.push_index(nid, meta, "Immunization", imm.id, date, f"{vaccine} (dose {dose})")

        self.stdout.write(self.style.SUCCESS(
            f"Grandi seeded: {len(PATIENTS)} patients, {n_cond} conditions, {n_vit} vitals sets, "
            f"{n_lab} lab reports, {n_res} lab results, {n_med} medications, {n_alg} allergies, "
            f"{n_imm} immunizations, {n_proc} procedures."))

    # -- idempotent writers (variant-B columns) ----------------------------
    def _patient(self, nid, demo):
        defaults = dict(
            first_name=demo["first"], last_name=demo["last"], dob=demo["dob"], gender=demo["gender"],
            phone=demo["phone"], mrn=f"GRA-{nid[-4:]}", address=demo["address"],
            blood_group=demo["blood_group"], marital_status=demo["marital"], occupation=demo["occupation"],
            ethnicity=demo["ethnicity"], emergency_contact_name=demo["ec_name"],
            emergency_contact_phone=demo["ec_phone"],
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
            patient=patient, department=ep["department"], visit_date=ep["date"],
            defaults={"physician": ep["physician"], "visit_category": ep["category"],
                      "chief_complaint": ep["complaint"]})
        return enc

    def _condition(self, patient, enc, text, icd, onset):
        obj, _ = Condition.objects.get_or_create(
            patient=patient, condition_desc=text, onset=onset,
            defaults={"encounter": enc, "icd_code": icd, "status": "active", "recorded": onset})
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

    def _procedure(self, patient, enc, name, snomed, cat, date, surgeon, outcome, notes):
        obj, _ = Procedure.objects.get_or_create(
            patient=patient, procedure_name=name, performed_date=date,
            defaults={"encounter": enc, "snomed_code": snomed, "category": cat,
                      "surgeon": surgeon, "outcome": outcome, "notes": notes})
        return obj

    def _immunization(self, patient, vaccine, cvx, dose, lot, site, route, date, by):
        obj, _ = Immunization.objects.get_or_create(
            patient=patient, vaccine_name=vaccine, administered_date=date,
            defaults={"cvx_code": cvx, "dose_number": dose, "lot_number": lot, "site": site,
                      "route": route, "administered_by": by})
        return obj
