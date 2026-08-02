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
    ("labtech@demo.np", "Lab Technician Bikash", Role.LAB_TECH, None),
    ("pharmacist@demo.np", "Pharmacist Rojina", Role.PHARMACIST, None),
]

# first, last, phone, dob, gender, blood_group, allergies, reg_by, portal_email, dept
DEMO_PATIENTS = [
    ("Ram", "Bahadur", "+977-9841000001", date(1970, 5, 12), Gender.MALE, "O+",
     ["Penicillin"], RegisteredBy.SELF, "ram@demo.np", Department.ENDOCRINOLOGY),
    ("Sita", "Kumari", "+977-9803000002", date(1988, 11, 23), Gender.FEMALE, "A+",
     [], RegisteredBy.RECEPTIONIST, None, Department.CARDIOLOGY),
    ("Hari", "Prasad", "+977-9841000003", date(1979, 2, 3), Gender.MALE, "B+",
     ["Aspirin"], RegisteredBy.RECEPTIONIST, None, Department.INFECTIOUS_DISEASES),
    ("Gita", "Devi", "+977-9803000004", date(2001, 7, 19), Gender.FEMALE, "AB+",
     [], RegisteredBy.SELF, "gita@demo.np", Department.NEPHROLOGY),
]

# National IDs (10-digit) assigned in order to the demo patients.
DEMO_NIDS = ["1234500001", "1234500002", "1234500003", "1234500004"]


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
