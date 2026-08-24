"""
Rich, realistic seed for Norvic International Hospital ("variant B" schema).

Norvic is modeled as a cardiac & multi-speciality centre. It deliberately shares
three patients with Nepal Mediciti (NIDs ...901, ...902, ...903) so the National
Platform can demonstrate a UNIFIED cross-hospital record for one citizen — the
same person seen at two hospitals, each contributing different encounters. Norvic
also has its own exclusive patients (...907, ...908).

On top of the shared clinical model, Norvic contributes TWO resource types that
Mediciti does not offer in this demo:
  * Immunization  — vaccination records (travel & routine clinic)
  * Procedure     — cardiac surgeries / interventions (CTVS)

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
PANELS = {
    "Complete Blood Count": [
        ("Hemoglobin", "718-7", "g/dL", "13.0-17.0", "14.5"),
        ("Total WBC Count", "6690-2", "10^3/uL", "4.0-11.0", "7.2"),
        ("Platelet Count", "777-3", "10^3/uL", "150-400", "250"),
        ("Hematocrit", "4544-3", "%", "40-50", "44"),
    ],
    "Lipid Profile": [
        ("Total Cholesterol", "2093-3", "mg/dL", "<200", "180"),
        ("LDL Cholesterol", "13457-7", "mg/dL", "<100", "90"),
        ("HDL Cholesterol", "2085-9", "mg/dL", ">40", "48"),
        ("Triglycerides", "2571-8", "mg/dL", "<150", "120"),
    ],
    "Blood Sugar": [
        ("Fasting Blood Glucose", "1558-6", "mg/dL", "70-100", "92"),
        ("HbA1c", "4548-4", "%", "4.0-5.6", "5.3"),
    ],
    "Cardiac Markers": [
        ("Troponin I", "10839-9", "ng/mL", "<0.04", "0.02"),
        ("CK-MB", "13969-1", "ng/mL", "<5.0", "2.5"),
        ("CRP", "1988-5", "mg/L", "<3.0", "1.5"),
        ("NT-proBNP", "33762-6", "pg/mL", "<125", "80"),
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
    "Renal Function Test": [
        ("Blood Urea", "3094-0", "mg/dL", "15-40", "28"),
        ("Serum Creatinine", "2160-0", "mg/dL", "0.7-1.3", "1.0"),
        ("eGFR", "33914-3", "mL/min", ">90", "95"),
    ],
}

# Canonical demographics. NIDs ...901/902/903 MUST match Mediciti's seed so the
# National Platform links them to one citizen. first/last split for variant B.
PATIENTS = {
    "2345678901": dict(
        first="Ram Bahadur", last="Thapa", dob="1970-05-12", gender="MALE", phone="9841000001",
        address="Kupondole, Lalitpur", blood_group="O+", marital="Married",
        occupation="Retired Teacher", ethnicity="Chhetri",
        ec_name="Sita Thapa", ec_phone="9800000011",
        allergies=[("Penicillin", "Skin rash", "moderate", "2015-04-10")],
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
    "2345678907": dict(
        first="Deepak", last="Tamang", dob="1965-09-17", gender="MALE", phone="9851000007",
        address="Bhaktapur", blood_group="A-", marital="Married",
        occupation="Retired Army", ethnicity="Tamang",
        ec_name="Nisha Tamang", ec_phone="9800000077",
        allergies=[],
    ),
    "2345678908": dict(
        first="Anjali", last="Pradhan", dob="1992-12-05", gender="FEMALE", phone="9861000008",
        address="Patan, Lalitpur", blood_group="O+", marital="Single",
        occupation="Software Engineer", ethnicity="Newar",
        ec_name="Rita Pradhan", ec_phone="9800000088",
        allergies=[("Latex", "Contact dermatitis", "mild", "2020-06-10")],
    ),
    # --- Cross-facility demo patients (NIDs ...09/.10 match Mediciti + both labs) ---
    "2345678909": dict(
        first="Laxmi Maya", last="Tamang", dob="1993-04-14", gender="FEMALE", phone="9842000001",
        address="Jhamsikhel, Lalitpur", blood_group="O+", marital="Single",
        occupation="Registered Nurse", ethnicity="Tamang",
        ec_name="Sunita Tamang", ec_phone="9800000099",
        allergies=[("Penicillin", "Skin rash", "moderate", "2015-02-10")],
    ),
    "2345678910": dict(
        first="Kiran Bahadur", last="Limbu", dob="1985-09-19", gender="MALE", phone="9842000002",
        address="Sundhara, Kathmandu", blood_group="A+", marital="Married",
        occupation="IT Manager", ethnicity="Limbu",
        ec_name="Roshni Limbu", ec_phone="9800000100",
        allergies=[("Iodinated contrast dye", "Urticaria", "mild", "2020-08-01")],
    ),
}

# Clinical journeys (variant-B fields are filled by the writers below).
JOURNEYS = {
    "2345678901": [  # Ram — also seen at Mediciti; here Norvic did his cardiac work-up
        dict(
            department="Cardiology", physician="Dr. Bibek Rajbhandari",
            date="2024-04-10", category="OPD", complaint="Exertional chest discomfort",
            conditions=[("Coronary Artery Disease", "I25.1", "2024-04-10")],
            vitals=dict(sbp=142, dbp=88, pulse=80, temp=36.6, spo2=97, rr=17, height=168, weight=73, bmi=25.9),
            labs=[
                ("Cardiac Markers", "2024-04-10", {"Troponin I": ("0.03", "N"), "NT-proBNP": ("210", "H"), "CRP": ("4.1", "H")}),
                ("Lipid Profile", "2024-04-10", {"Total Cholesterol": ("224", "H"), "LDL Cholesterol": ("150", "H"), "HDL Cholesterol": ("39", "L")}),
            ],
            meds=[("Atorvastatin", "83367", "40 mg", "once daily at night", "oral", "ongoing"),
                  ("Aspirin", "1191", "75 mg", "once daily", "oral", "ongoing")],
        ),
    ],
    "2345678903": [  # Hari — cardiac interventions done AT NORVIC (Procedures live here)
        dict(
            department="Cardiology", physician="Dr. Bibek Rajbhandari",
            date="2024-01-24", category="Inpatient", complaint="Post-MI revascularization",
            conditions=[("Coronary Artery Disease", "I25.1", "2024-01-22"),
                        ("ST-Elevation Myocardial Infarction", "I21.0", "2024-01-22")],
            vitals=dict(sbp=150, dbp=94, pulse=96, temp=36.8, spo2=94, rr=20, height=172, weight=79, bmi=26.7),
            labs=[
                ("Cardiac Markers", "2024-01-24", {"Troponin I": ("4.6", "H"), "CK-MB": ("30", "H"), "NT-proBNP": ("680", "H")}),
                ("Coagulation Profile", "2024-01-24", {"INR": ("1.1", "N"), "Prothrombin Time": ("12.4", "N")}),
            ],
            meds=[("Ticagrelor", "1116632", "90 mg", "twice daily", "oral", "12 months"),
                  ("Atorvastatin", "83367", "80 mg", "once daily at night", "oral", "ongoing")],
            procedures=[
                ("Percutaneous Coronary Intervention (PCI) with drug-eluting stent to LAD",
                 "415070008", "Cardiac Intervention", "2024-01-24", "Dr. Bibek Rajbhandari",
                 "Successful, TIMI-3 flow restored", "Single DES to proximal LAD; no complications."),
            ],
        ),
    ],
    "2345678907": [  # Deepak — Norvic-only, valvular heart disease -> valve replacement
        dict(
            department="Cardiothoracic & Vascular Surgery (CTVS)", physician="Dr. Manish Shakya",
            date="2023-05-15", category="Inpatient", complaint="Progressive breathlessness, murmur",
            conditions=[("Severe Aortic Stenosis", "I35.0", "2022-11-01"),
                        ("Atrial Fibrillation", "I48.0", "2023-05-15")],
            vitals=dict(sbp=138, dbp=82, pulse=88, temp=36.7, spo2=95, rr=19, height=170, weight=68, bmi=23.5),
            labs=[
                ("Coagulation Profile", "2023-05-15", {"INR": ("2.4", "H"), "Prothrombin Time": ("22.0", "H")}),
                ("Complete Blood Count", "2023-05-15", {"Hemoglobin": ("12.8", "L"), "Platelet Count": ("210", "N")}),
                ("Electrolytes", "2023-05-15", {"Potassium": ("4.4", "N"), "Sodium": ("139", "N")}),
            ],
            meds=[("Warfarin", "11289", "5 mg", "once daily", "oral", "ongoing"),
                  ("Bisoprolol", "19484", "5 mg", "once daily", "oral", "ongoing")],
            procedures=[
                ("Aortic Valve Replacement (mechanical prosthesis)",
                 "232717009", "Cardiac Surgery", "2023-05-18", "Dr. Manish Shakya",
                 "Successful, uneventful recovery", "On-pump AVR; mechanical valve; lifelong anticoagulation advised."),
            ],
        ),
        dict(
            department="Cardiology", physician="Dr. Bibek Rajbhandari",
            date="2024-06-02", category="OPD", complaint="Anticoagulation follow-up",
            conditions=[],
            vitals=dict(sbp=130, dbp=80, pulse=72, temp=36.5, spo2=98, rr=16, height=170, weight=69, bmi=23.9),
            labs=[
                ("Coagulation Profile", "2024-06-02", {"INR": ("2.6", "H"), "Prothrombin Time": ("24.1", "H")}),
            ],
            meds=[],
        ),
    ],
    "2345678908": [  # Anjali — Norvic-only, travel medicine + minor procedure
        dict(
            department="General Medicine & Travel Clinic", physician="Dr. Sabin Maharjan",
            date="2024-08-20", category="OPD", complaint="Pre-travel vaccination and check-up",
            conditions=[("Iron Deficiency Anemia", "D50.9", "2024-08-20")],
            vitals=dict(sbp=112, dbp=72, pulse=76, temp=36.6, spo2=99, rr=15, height=162, weight=55, bmi=21.0),
            labs=[
                ("Complete Blood Count", "2024-08-20", {"Hemoglobin": ("10.6", "L"), "Hematocrit": ("34", "L")}),
            ],
            meds=[("Ferrous Ascorbate", "310965", "100 mg", "once daily", "oral", "3 months")],
            procedures=[
                ("Excision of sebaceous cyst (minor surgery)",
                 "50324007", "Minor Surgery", "2024-08-20", "Dr. Sabin Maharjan",
                 "Successful, sutured", "Local anaesthesia; wound review in 7 days."),
            ],
        ),
    ],
    "2345678909": [  # Laxmi — also at Mediciti; here Norvic did her pre-marriage work-up
        dict(
            department="General Medicine & Travel Clinic", physician="Dr. Sabin Maharjan",
            date="2024-09-02", category="OPD", complaint="Pre-marriage check-up, easy fatigability",
            conditions=[("Iron Deficiency Anemia", "D50.9", "2024-09-02"),
                        ("Subclinical Hypothyroidism", "E03.9", "2024-09-02")],
            vitals=dict(sbp=110, dbp=70, pulse=74, temp=36.5, spo2=99, rr=15, height=160, weight=55, bmi=21.5),
            labs=[
                ("Complete Blood Count", "2024-09-02", {"Hemoglobin": ("10.8", "L"), "Hematocrit": ("35", "L"), "Platelet Count": ("240", "N")}),
            ],
            meds=[("Ferrous Ascorbate", "310965", "100 mg", "once daily", "oral", "3 months")],
        ),
    ],
    "2345678910": [  # Kiran — also at Mediciti; Norvic's cardiology assessed his chest pain
        dict(
            department="Cardiology", physician="Dr. Bibek Rajbhandari",
            date="2024-05-14", category="OPD", complaint="Atypical chest pain, diabetes follow-up",
            conditions=[("Coronary Artery Disease", "I25.1", "2024-05-14"),
                        ("Type 2 Diabetes Mellitus", "E11.9", "2023-06-08")],
            vitals=dict(sbp=140, dbp=90, pulse=84, temp=36.6, spo2=97, rr=16, height=176, weight=96, bmi=31.0),
            labs=[
                ("Cardiac Markers", "2024-05-14", {"Troponin I": ("0.02", "N"), "NT-proBNP": ("96", "N"), "CRP": ("2.2", "N")}),
                ("Blood Sugar", "2024-05-14", {"Fasting Blood Glucose": ("118", "H"), "HbA1c": ("6.4", "H")}),
            ],
            meds=[("Atorvastatin", "83367", "20 mg", "once daily at night", "oral", "ongoing"),
                  ("Metformin", "6809", "850 mg", "twice daily", "oral", "ongoing")],
        ),
    ],
}

# Immunizations per patient: (vaccine, cvx, dose, lot, site, route, date, by)
IMMUNIZATIONS = {
    "2345678901": [
        ("Influenza, seasonal", "141", "Annual", "FLU2024-88", "Left deltoid", "Intramuscular", "2024-04-10", "Nurse R. Lama"),
    ],
    "2345678903": [
        ("COVID-19 (Covishield)", "210", "Booster", "COV-BST-33", "Left deltoid", "Intramuscular", "2023-02-11", "Nurse P. Gurung"),
    ],
    "2345678907": [
        ("Pneumococcal (PCV13)", "133", "1", "PCV-2023-12", "Right deltoid", "Intramuscular", "2023-05-20", "Nurse R. Lama"),
        ("Influenza, seasonal", "141", "Annual", "FLU2023-51", "Left deltoid", "Intramuscular", "2023-10-05", "Nurse R. Lama"),
    ],
    "2345678908": [
        ("Hepatitis A", "52", "1", "HEPA-2024-07", "Left deltoid", "Intramuscular", "2024-08-20", "Nurse S. Thapa"),
        ("Typhoid (Vi polysaccharide)", "101", "1", "TYP-2024-19", "Left deltoid", "Intramuscular", "2024-08-20", "Nurse S. Thapa"),
        ("COVID-19 (Covishield)", "210", "2", "COV-2021-77", "Right deltoid", "Intramuscular", "2021-08-14", "Nurse S. Thapa"),
    ],
    "2345678909": [
        ("Tetanus-diphtheria (Td)", "5", "Booster", "TD-2024-31", "Left deltoid", "Intramuscular", "2024-09-02", "Nurse S. Thapa"),
        ("Influenza, seasonal", "141", "Annual", "FLU2024-92", "Right deltoid", "Intramuscular", "2024-09-02", "Nurse S. Thapa"),
    ],
    "2345678910": [
        ("Influenza, seasonal", "141", "Annual", "FLU2024-95", "Left deltoid", "Intramuscular", "2024-05-14", "Nurse R. Lama"),
    ],
}


class Command(BaseCommand):
    help = "Rich, idempotent seed for Norvic International Hospital."

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
            f"Norvic seeded: {len(PATIENTS)} patients, {n_cond} conditions, {n_vit} vitals sets, "
            f"{n_lab} lab reports, {n_res} lab results, {n_med} medications, {n_alg} allergies, "
            f"{n_imm} immunizations, {n_proc} procedures."))

    # -- idempotent writers (variant-B columns) ----------------------------
    def _patient(self, nid, demo):
        defaults = dict(
            first_name=demo["first"], last_name=demo["last"], dob=demo["dob"], gender=demo["gender"],
            phone=demo["phone"], mrn=f"NOR-{nid[-4:]}", address=demo["address"],
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
