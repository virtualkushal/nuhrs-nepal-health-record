"""
Seed a full set of demo data for local exploration of the whole frontend (v2).

Creates one staff login for EVERY role (email login) plus sample patients with
full clinical history: encounters across departments, nurse vitals, ICD-10
diagnoses, lab orders + results (quantitative trends + report-type), and
prescriptions.

Usage:
    python manage.py seed_demo

All demo accounts use the password:  demo12345
Login is by EMAIL, e.g.  doctor@demo.np / demo12345
Local development only — never run against production.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.constants import (
    Department,
    DiagnosisStatus,
    EncounterStatus,
    Gender,
    LabOrderStatus,
    LabResultType,
    PrescriptionStatus,
    RegisteredBy,
    Role,
    StaffStatus,
)
from core.models import (
    Diagnosis,
    Encounter,
    LabOrder,
    LabReport,
    LabResult,
    Patient,
    Prescription,
    Vitals,
)

Staff = get_user_model()

DEMO_PASSWORD = "demo12345"

# email, full name, role, department
DEMO_STAFF = [
    ("admin@demo.np", "System Administrator", Role.ADMIN, None),
    ("reception@demo.np", "Receptionist Gita", Role.RECEPTIONIST, None),
    ("nurse@demo.np", "Nurse Kabita Rai", Role.NURSE, None),
    ("doctor@demo.np", "Dr. Anjali Sharma", Role.DOCTOR, Department.ENDOCRINOLOGY),
    ("doctor2@demo.np", "Dr. Bikram Thapa", Role.DOCTOR, Department.CARDIOLOGY),
    ("doctor3@demo.np", "Dr. Sabina Gurung", Role.DOCTOR, Department.INFECTIOUS_DISEASES),
    # One doctor per remaining department so reception can check patients into
    # ANY of the 7 departments and a doctor queue exists to receive them
    # (the doctor queue filters encounters to the doctor's own department).
    ("doctor4@demo.np", "Dr. Prakash Neupane", Role.DOCTOR, Department.NEPHROLOGY),
    ("doctor5@demo.np", "Dr. Sunita Karki", Role.DOCTOR, Department.INTERNAL_MEDICINE),
    ("doctor6@demo.np", "Dr. Rajesh Hamal", Role.DOCTOR, Department.GASTROENTEROLOGY),
    ("doctor7@demo.np", "Dr. Mina Shrestha", Role.DOCTOR, Department.HEMATOLOGY),
    ("labtech@demo.np", "Lab Technician Bikash", Role.LAB_TECH, None),
    ("pharmacist@demo.np", "Pharmacist Rojina", Role.PHARMACIST, None),
]

# first, last, phone, dob, gender, blood_group, allergies, reg_by, portal_email, dept
DEMO_PATIENTS = [
    ("Ram", "Bahadur", "9841000001", date(1970, 5, 12), Gender.MALE, "O+",
     ["Penicillin"], RegisteredBy.SELF, "ram@demo.np", Department.ENDOCRINOLOGY),
    ("Sita", "Kumari", "9803000002", date(1988, 11, 23), Gender.FEMALE, "A+",
     [], RegisteredBy.RECEPTIONIST, None, Department.CARDIOLOGY),
    ("Hari", "Prasad", "9841000003", date(1979, 2, 3), Gender.MALE, "B+",
     ["Aspirin"], RegisteredBy.RECEPTIONIST, None, Department.INFECTIOUS_DISEASES),
    ("Gita", "Devi", "9803000004", date(2001, 7, 19), Gender.FEMALE, "AB+",
     [], RegisteredBy.SELF, "gita@demo.np", Department.NEPHROLOGY),
    # --- Expanded federation cohort (NIDs ...12/...18/...22/...28/...30).
    # Names / phones / DOBs are CANONICAL and MUST match the Mediciti, Norvic and
    # lab seeds. No portal account: these demo the self-activation flow. ---
    ("Kamala Devi", "Bhattarai", "9841000012", date(1974, 8, 15), Gender.FEMALE, "O+",
     [], RegisteredBy.RECEPTIONIST, None, Department.ENDOCRINOLOGY),
    ("Mina Kumari", "Adhikari", "9841000018", date(1986, 12, 12), Gender.FEMALE, "A-",
     [], RegisteredBy.RECEPTIONIST, None, Department.ENDOCRINOLOGY),
    ("Sabina", "Karki", "9841000022", date(1992, 10, 3), Gender.FEMALE, "O+",
     [], RegisteredBy.SELF, None, Department.ENDOCRINOLOGY),
    ("Rekha Devi", "Mishra", "9841000028", date(1972, 5, 7), Gender.FEMALE, "AB-",
     [], RegisteredBy.RECEPTIONIST, None, Department.NEPHROLOGY),
    ("Bimala", "Thapa Chhetri", "9841000030", date(1997, 3, 28), Gender.FEMALE, "O+",
     [], RegisteredBy.SELF, None, Department.HEMATOLOGY),
]

# National IDs (10-digit Nepal NIN) assigned in order to the demo patients.
# The first three match the NUHRS hospital/lab seed NIDs so the same patient is
# recognisable across SwasthyaEHR and the national exchange demo.
DEMO_NIDS = [
    "2345678901", "2345678902", "2345678903", "2345678904",
    # Expanded cohort — same order as the DEMO_PATIENTS rows above.
    "2345678912", "2345678918", "2345678922", "2345678928", "2345678930",
]



class Command(BaseCommand):
    help = "Create demo staff (one per role) and patients with full clinical history."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding demo staff..."))
        staff_by_role = {}
        doctors_by_dept = {}
        for email, full_name, role, dept in DEMO_STAFF:
            staff, created = Staff.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "role": role,
                    "department": dept,
                    "status": StaffStatus.ACTIVE,
                    "is_active": True,
                    "must_change_password": False,
                    "is_staff": role == Role.ADMIN,
                    "is_superuser": role == Role.ADMIN,
                },
            )
            if created:
                staff.set_password(DEMO_PASSWORD)
                staff.save()
                self.stdout.write(self.style.SUCCESS(f"  + {email:<20} ({role})"))
            else:
                self.stdout.write(self.style.WARNING(f"  = {email:<20} exists — skipped"))
            staff_by_role.setdefault(role, staff)
            if role == Role.DOCTOR:
                doctors_by_dept[dept] = staff

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding demo patients..."))
        for idx, (
            first, last, phone, dob, gender, blood, allergies, reg_by, portal, dept
        ) in enumerate(DEMO_PATIENTS):
            nid = DEMO_NIDS[idx]
            patient = Patient.objects.filter(national_id=nid).first()
            if patient is not None:
                self.stdout.write(self.style.WARNING(f"  = {first} {last} exists — reusing"))
            else:
                user = None
                if portal and not Staff.objects.filter(email=portal).exists():
                    user = Staff.objects.create(
                        email=portal,
                        full_name=f"{first} {last}",
                        role=Role.PATIENT,
                        status=StaffStatus.ACTIVE,
                        is_active=True,
                        must_change_password=False,
                    )
                    user.set_password(DEMO_PASSWORD)
                    user.save()
                patient = Patient.objects.create(
                    user=user,
                    national_id=nid,
                    first_name=first,
                    last_name=last,
                    phone_number=phone,
                    date_of_birth=dob,
                    gender=gender,
                    blood_group=blood,
                    allergies=allergies,
                    registered_by=reg_by,
                )
                note = f" [portal: {portal}]" if user else ""
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  + {first} {last} ({patient.hospital_identifier}) NID={nid}{note}"
                    )
                )
            self._seed_clinical_history(patient, dept, staff_by_role, doctors_by_dept)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo data ready. Log in at /login with EMAIL:"))
        for email, _n, role, _d in DEMO_STAFF:
            self.stdout.write(f"    {email:<20} / {DEMO_PASSWORD}   -> {role}")
        for *_r, portal, _d in DEMO_PATIENTS:
            if portal:
                self.stdout.write(f"    {portal:<20} / {DEMO_PASSWORD}   -> PATIENT")

    def _seed_clinical_history(self, patient, dept, staff_by_role, doctors_by_dept):
        if Encounter.objects.filter(patient=patient).exists():
            self.stdout.write(
                self.style.WARNING(f"    = {patient.first_name}'s history already seeded")
            )
            return

        receptionist = staff_by_role.get(Role.RECEPTIONIST)
        nurse = staff_by_role.get(Role.NURSE)
        doctor = doctors_by_dept.get(dept) or staff_by_role.get(Role.DOCTOR)
        labtech = staff_by_role.get(Role.LAB_TECH)
        pharmacist = staff_by_role.get(Role.PHARMACIST)
        now = timezone.now()

        # A closed historical encounter with vitals, diagnosis, labs, rx.
        enc = Encounter.objects.create(
            patient=patient,
            department=dept,
            attending_doctor=doctor,
            created_by=receptionist,
            chief_complaint="Routine follow-up and blood work.",
            status=EncounterStatus.CLOSED,
        )

        Vitals.objects.create(
            encounter=enc,
            recorded_by=nurse,
            height_cm=168,
            weight_kg=72,
            systolic_bp=128,
            diastolic_bp=82,
            pulse=78,
            temperature_c=36.8,
            spo2=98,
        )

        # A department-appropriate diagnosis (first ICD-10 code for the dept).
        from core.constants import ICD10

        dept_codes = list(ICD10.for_department(dept).keys())
        if dept_codes:
            Diagnosis.objects.create(
                encounter=enc,
                patient=patient,
                diagnosed_by=doctor,
                icd10_code=dept_codes[0],
                clinical_status=DiagnosisStatus.ACTIVE,
                notes="Recorded during demo seed.",
            )

        # Quantitative lab trend: 3 Hemoglobin + 2 FBS readings across ~5 weeks.
        lab_points = [
            ("HEMOGLOBIN", "12.10", 35),
            ("HEMOGLOBIN", "13.40", 21),
            ("HEMOGLOBIN", "14.20", 3),
            ("FBS", "95.00", 21),
            ("FBS", "110.00", 3),
        ]
        for test_code, value, days_ago in lab_points:
            order = LabOrder.objects.create(
                encounter=enc,
                patient=patient,
                ordered_by=doctor,
                test_code=test_code,
                status=LabOrderStatus.COMPLETED,
            )
            report = LabReport.objects.create(
                lab_order=order,
                patient=patient,
                entered_by=labtech,
                status=LabReport.CONFIRMED,
            )
            res = LabResult.objects.create(
                lab_report=report,
                patient=patient,
                test_code=test_code,
                result_value=value,
            )
            stamp = now - timedelta(days=days_ago)
            LabResult.objects.filter(pk=res.pk).update(created_at=stamp)
            LabOrder.objects.filter(pk=order.pk).update(created_at=stamp)

        # A report-type result (blood group).
        order = LabOrder.objects.create(
            encounter=enc, patient=patient, ordered_by=doctor,
            test_code="BLOOD_GROUP", status=LabOrderStatus.COMPLETED,
        )
        report = LabReport.objects.create(
            lab_order=order, patient=patient, entered_by=labtech,
            status=LabReport.CONFIRMED,
        )
        LabResult.objects.create(
            lab_report=report, patient=patient, test_code="BLOOD_GROUP",
            report_text=f"Blood group {patient.blood_group}.",
        )

        # Nepal-endemic showcase: give Infectious Diseases patients a Scrub
        # Typhus case with its serology test + D-Dimer, so the newly added
        # endemic catalog entries appear in the demo and the FHIR bundle.
        if dept == Department.INFECTIOUS_DISEASES:
            Diagnosis.objects.create(
                encounter=enc,
                patient=patient,
                diagnosed_by=doctor,
                icd10_code="A75.9",  # Scrub typhus / rickettsial fever
                clinical_status=DiagnosisStatus.ACTIVE,
                notes="High-grade fever with eschar; endemic scrub typhus.",
            )
            st_order = LabOrder.objects.create(
                encounter=enc, patient=patient, ordered_by=doctor,
                test_code="SCRUB_TYPHUS_IGM", status=LabOrderStatus.COMPLETED,
            )
            st_report = LabReport.objects.create(
                lab_order=st_order, patient=patient, entered_by=labtech,
                status=LabReport.CONFIRMED,
            )
            LabResult.objects.create(
                lab_report=st_report, patient=patient, test_code="SCRUB_TYPHUS_IGM",
                report_text="Scrub Typhus IgM: POSITIVE (ELISA).",
            )
            dd_order = LabOrder.objects.create(
                encounter=enc, patient=patient, ordered_by=doctor,
                test_code="D_DIMER", status=LabOrderStatus.COMPLETED,
            )
            dd_report = LabReport.objects.create(
                lab_order=dd_order, patient=patient, entered_by=labtech,
                status=LabReport.CONFIRMED,
            )
            LabResult.objects.create(
                lab_report=dd_report, patient=patient, test_code="D_DIMER",
                result_value="820.00",
            )

        # Prescriptions: one fulfilled, one active in the pharmacy queue.

        rx_data = [
            ("Paracetamol 500mg", "1 tablet every 6 hours for 3 days",
             PrescriptionStatus.COMPLETED, 20),
            ("Amlodipine 5mg", "1 tablet once daily", PrescriptionStatus.ACTIVE, 2),
        ]
        for med, dosage, rx_status, days_ago in rx_data:
            rx = Prescription.objects.create(
                encounter=enc,
                patient=patient,
                prescribed_by=doctor,
                medication_name=med,
                dosage_instruction=dosage,
                status=rx_status,
            )
            stamp = now - timedelta(days=days_ago)
            if rx_status == PrescriptionStatus.COMPLETED:
                rx.fulfilled_by = pharmacist
                rx.fulfilled_at = stamp
                rx.save(update_fields=["fulfilled_by", "fulfilled_at"])
            Prescription.objects.filter(pk=rx.pk).update(created_at=stamp)

        self.stdout.write(
            self.style.SUCCESS(f"    + clinical history for {patient.first_name}")
        )
