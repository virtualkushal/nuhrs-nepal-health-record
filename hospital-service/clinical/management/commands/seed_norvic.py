"""
Rich, realistic seed for Norvic International Hospital (variant B / HOSP002).

Norvic stores the SAME kinds of clinical facts as Mediciti but in a DIFFERENT
column layout (first_name/last_name, physician/visit_date, condition_desc/
icd_code, measurement_name ...). This seed writes those variant-B columns; the
NorvicFHIRAdapter then emits FHIR identical in shape to Mediciti's — which is the
whole point of the standard.

Cross-hospital story: patients 12345678901 (Ram) and 12345678903 (Hari) also
have records at Mediciti, so the National Platform shows a COMBINED history from
both hospitals for the same national ID. Norvic also has its own patients
(907, 908, 909).

The shared clinical tables (Allergy, Vitals, LabOrder/Report/Result,
MedicationRequest) are identical across variants, so we reuse the same writers
and the shared lab panel catalogue from seed_mediciti.

Every writer is IDEMPOTENT — safe to run repeatedly.

Run:  python manage.py seed_norvic
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from clinical import services
from clinical.management.commands.seed_mediciti import PANELS
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

# ---------------------------------------------------------------------------
# Canonical demographics.  NIDs 901 & 903 MUST match Mediciti/other services.
# ---------------------------------------------------------------------------
PATIENTS = {
    "12345678901": dict(  # shared with Mediciti — Ram
        name="Ram Bahadur Thapa", dob="1970-05-12", gender="MALE", phone="9841000001",
        address="Kupondole, Lalitpur", blood_group="O+", marital="Married",
        occupation="Retired Teacher", ethnicity="Chhetri",
        ec_name="Sita Thapa", ec_phone="9800000011",
        allergies=[("Penicillin", "Skin rash", "moderate", "2015-04-10")],
    ),
    "12345678903": dict(  # shared with Mediciti — Hari
        name="Hari Prasad Koirala", dob="1979-02-03", gender="MALE", phone="9841000003",
        address="Biratnagar, Morang", blood_group="B+", marital="Married",
        occupation="Businessman", ethnicity="Brahmin",
        ec_name="Radha Koirala", ec_phone="9800000033",
        allergies=[("Sulfonamides", "Urticaria", "severe", "2018-09-01")],
    ),
    "12345678907": dict(  # Norvic-only
        name="Anjali Tamang", dob="1991-04-27", gender="FEMALE", phone="9808000007",
        address="Jawalakhel, Lalitpur", blood_group="A-", marital="Married",
        occupation="Software Engineer", ethnicity="Tamang",
        ec_name="Raju Tamang", ec_phone="9800000077",
        allergies=[],
    ),
    "12345678908": dict(  # Norvic-only
        name="Deepak Karki", dob="1968-09-15", gender="MALE", phone="9818000008",
        address="Maharajgunj, Kathmandu", blood_group="O+", marital="Married",
        occupation="Civil Engineer", ethnicity="Chhetri",
        ec_name="Nirmala Karki", ec_phone="9800000088",
        allergies=[("Iodine Contrast", "Hives", "moderate", "2020-06-12")],
    ),
    "12345678909": dict(  # Norvic-only
        name="Sunita Magar", dob="1985-12-02", gender="FEMALE", phone="9828000009",
        address="Butwal, Rupandehi", blood_group="AB+", marital="Married",
        occupation="Teacher", ethnicity="Magar",
        ec_name="Bhim Magar", ec_phone="9800000099",
        allergies=[],
    ),
}

# ---------------------------------------------------------------------------
# Clinical journeys.  Each episode:
#   dept (used as visit_category label), doctor, date, type, reason,
#   conditions: [(text, icd10, onset)],
#   vitals: {...},  labs: [(panel, date, {test:(value,interp)})],  meds: [...]
# ---------------------------------------------------------------------------
JOURNEYS = {
    "12345678901": [  # Ram at Norvic — orthopedic + eye (complements Mediciti diabetes)
        dict(
            dept="Orthopaedics & Joint Replacement", doctor="Dr. Bibek Shrestha",
            date="2023-09-12", type="OPD", reason="Right knee pain, difficulty walking",
            conditions=[("Osteoarthritis of Knee", "M17.0", "2022-05-01"),
                        ("Vitamin D Deficiency", "E55.9", "2023-09-12")],
            vitals=dict(sbp=140, dbp=86, pulse=76, temp=36.6, spo2=98, rr=16, height=168, weight=73, bmi=25.9),
            labs=[
                ("Complete Blood Count", "2023-09-12", {"Hemoglobin": ("13.8", "N"), "Total WBC Count": ("7.8", "N")}),
            ],
            meds=[("Cholecalciferol (Vitamin D3)", "2418", "60000 IU", "once weekly", "oral", "8 weeks"),
                  ("Glucosamine", "882504", "500 mg", "three times daily", "oral", "ongoing")],
        ),
        dict(
            dept="Ophthalmology", doctor="Dr. Kriti Rana",
            date="2024-04-18", type="OPD", reason="Blurred vision, diabetic eye screening",
            conditions=[("Diabetic Retinopathy", "E11.31", "2024-04-18")],
            vitals=dict(sbp=138, dbp=84, pulse=74, temp=36.5, spo2=98, rr=15, height=168, weight=72, bmi=25.5),
            labs=[],
            meds=[],
        ),
    ],
    "12345678903": [  # Hari at Norvic — neurology (complements Mediciti cardiac)
        dict(
            dept="Neurology", doctor="Dr. Prashanna Joshi",
            date="2023-02-14", type="OPD", reason="Recurrent headache, transient weakness",
            conditions=[("Transient Ischemic Attack", "G45.9", "2023-02-14"),
                        ("Hyperlipidemia", "E78.5", "2020-08-10")],
            vitals=dict(sbp=150, dbp=94, pulse=82, temp=36.7, spo2=97, rr=17, height=172, weight=79, bmi=26.7),
            labs=[
                ("Lipid Profile", "2023-02-14", {"Total Cholesterol": ("236", "H"), "LDL Cholesterol": ("162", "H"), "HDL Cholesterol": ("36", "L"), "Triglycerides": ("224", "H")}),
                ("Coagulation Profile", "2023-02-14", {"Prothrombin Time": ("12.4", "N"), "INR": ("1.0", "N")}),
            ],
            meds=[("Aspirin", "1191", "75 mg", "once daily", "oral", "ongoing"),
                  ("Rosuvastatin", "301542", "10 mg", "once daily at night", "oral", "ongoing")],
        ),
    ],
    "12345678907": [  # Anjali — obstetric / thyroid
        dict(
            dept="Obstetrics & Gynaecology", doctor="Dr. Meena Pandey",
            date="2024-06-05", type="OPD", reason="Antenatal check-up",
            conditions=[("Anemia in Pregnancy", "O99.0", "2024-06-05"),
                        ("Hypothyroidism", "E03.9", "2022-01-10")],
            vitals=dict(sbp=110, dbp=70, pulse=84, temp=36.6, spo2=99, rr=16, height=162, weight=61, bmi=23.2),
            labs=[
                ("Complete Blood Count", "2024-06-05", {"Hemoglobin": ("10.4", "L"), "Hematocrit": ("34", "L")}),
                ("Thyroid Function Test", "2024-06-05", {"TSH": ("4.6", "H"), "Free T4": ("0.9", "N")}),
                ("Iron Studies", "2024-06-05", {"Serum Iron": ("46", "L"), "Ferritin": ("20", "L")}),
            ],
            meds=[("Ferrous Ascorbate", "310966", "100 mg", "once daily", "oral", "ongoing"),
                  ("Folic Acid", "4511", "5 mg", "once daily", "oral", "ongoing"),
                  ("Levothyroxine", "10582", "50 mcg", "once daily before breakfast", "oral", "ongoing")],
        ),
    ],
    "12345678908": [  # Deepak — cardiology (stent) + diabetes
        dict(
            dept="Cardiology & Cardiac Cath Lab", doctor="Dr. Anup Baral",
            date="2022-10-03", type="Inpatient", reason="Unstable angina, admitted for angiography",
            conditions=[("Coronary Artery Disease", "I25.1", "2022-10-03"),
                        ("Type 2 Diabetes Mellitus", "E11.9", "2018-07-01"),
                        ("Essential Hypertension", "I10", "2016-01-01")],
            vitals=dict(sbp=156, dbp=96, pulse=90, temp=36.8, spo2=96, rr=18, height=170, weight=82, bmi=28.4),
            labs=[
                ("Cardiac Markers", "2022-10-03", {"Troponin I": ("1.2", "H"), "CK-MB": ("14", "H"), "CRP": ("8.4", "H")}),
                ("Lipid Profile", "2022-10-03", {"Total Cholesterol": ("242", "H"), "LDL Cholesterol": ("166", "H"), "HDL Cholesterol": ("35", "L")}),
                ("Blood Sugar", "2022-10-03", {"Fasting Blood Glucose": ("168", "H"), "HbA1c": ("8.2", "H")}),
            ],
            meds=[("Aspirin", "1191", "75 mg", "once daily", "oral", "ongoing"),
                  ("Ticagrelor", "1116632", "90 mg", "twice daily", "oral", "12 months"),
                  ("Atorvastatin", "83367", "40 mg", "once daily at night", "oral", "ongoing"),
                  ("Metformin", "6809", "1000 mg", "twice daily", "oral", "ongoing")],
        ),
        dict(
            dept="Cardiology & Cardiac Cath Lab", doctor="Dr. Anup Baral",
            date="2024-03-11", type="OPD", reason="Post-PCI follow-up",
            conditions=[("Status Post Coronary Stent", "Z95.5", "2022-10-05")],
            vitals=dict(sbp=134, dbp=82, pulse=72, temp=36.5, spo2=98, rr=16, height=170, weight=80, bmi=27.7),
            labs=[
                ("Blood Sugar", "2024-03-11", {"Fasting Blood Glucose": ("138", "H"), "HbA1c": ("7.1", "H")}),
                ("Lipid Profile", "2024-03-11", {"Total Cholesterol": ("176", "N"), "LDL Cholesterol": ("88", "N"), "HDL Cholesterol": ("42", "N")}),
            ],
            meds=[],
        ),
    ],
    "12345678909": [  # Sunita — oncology (breast) + surgery
        dict(
            dept="Oncology & Cancer Care", doctor="Dr. Sabina Thapa",
            date="2023-11-08", type="Inpatient", reason="Breast lump, biopsy positive",
            conditions=[("Carcinoma of Breast", "C50.9", "2023-11-08"),
                        ("Iron Deficiency Anemia", "D50.9", "2023-11-08")],
            vitals=dict(sbp=118, dbp=76, pulse=86, temp=36.7, spo2=98, rr=17, height=158, weight=56, bmi=22.4),
            labs=[
                ("Complete Blood Count", "2023-11-08", {"Hemoglobin": ("10.6", "L"), "Total WBC Count": ("6.4", "N"), "Platelet Count": ("240", "N")}),
                ("Liver Function Test", "2023-11-08", {"SGPT (ALT)": ("28", "N"), "SGOT (AST)": ("24", "N"), "Serum Albumin": ("3.6", "N")}),
                ("Renal Function Test", "2023-11-08", {"Serum Creatinine": ("0.9", "N"), "eGFR": ("98", "N")}),
            ],
            meds=[("Doxorubicin", "3639", "60 mg/m2", "every 3 weeks", "IV", "6 cycles"),
                  ("Cyclophosphamide", "3002", "600 mg/m2", "every 3 weeks", "IV", "6 cycles"),
                  ("Ondansetron", "26225", "8 mg", "before chemotherapy", "IV", "as needed")],
        ),
        dict(
            dept="Oncology & Cancer Care", doctor="Dr. Sabina Thapa",
            date="2024-05-20", type="OPD", reason="Post-chemotherapy review",
            conditions=[],
            vitals=dict(sbp=116, dbp=74, pulse=80, temp=36.6, spo2=99, rr=16, height=158, weight=58, bmi=23.2),
            labs=[
                ("Complete Blood Count", "2024-05-20", {"Hemoglobin": ("11.8", "L"), "Total WBC Count": ("5.2", "N"), "Platelet Count": ("260", "N")}),
            ],
            meds=[("Tamoxifen", "10324", "20 mg", "once daily", "oral", "5 years")],
        ),
    ],
}


class Command(BaseCommand):
    help = "Rich, idempotent seed for Norvic International Hospital (variant B)."

    def handle(self, *args, **options):
        if settings.ORG_CODE != "HOSP002":
            self.stdout.write(self.style.WARNING(
                f"seed_norvic is only for HOSP002 (Norvic). This is {settings.ORG_CODE}. Skipping."))
            return
        if settings.SCHEMA_VARIANT != "B":
            self.stdout.write(self.style.WARNING("seed_norvic expects variant B. Skipping."))
            return

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
            f"Norvic seeded: {len(PATIENTS)} patients, {n_cond} conditions, {n_vit} vitals sets, "
            f"{n_lab} lab reports, {n_res} lab results, {n_med} medications, {n_alg} allergies."))

    # -- variant-B idempotent writers --------------------------------------
    def _patient(self, nid, demo):
        parts = demo["name"].split(" ", 1)
        defaults = dict(
            first_name=parts[0], last_name=parts[1] if len(parts) > 1 else "",
            dob=demo["dob"], gender=demo["gender"], phone=demo["phone"],
            mrn=f"NOR-{nid[-4:]}", address=demo["address"], blood_group=demo["blood_group"],
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
        # Variant B columns: physician / visit_date / visit_category / chief_complaint
        enc, _ = Encounter.objects.get_or_create(
            patient=patient, visit_date=ep["date"], chief_complaint=ep["reason"],
            defaults={"physician": ep["doctor"], "visit_category": ep["type"]})
        return enc

    def _condition(self, patient, enc, text, icd, onset):
        # Variant B columns: condition_desc / icd_code / status / onset / recorded
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
