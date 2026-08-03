"""
Seed this hospital instance with demo patients + clinical records, and push each
record's metadata to the National Platform so it becomes discoverable.

The same shared NIDs are used across hospitals/labs so a single patient has a
cross-organization history — this is what makes the exchange demo compelling.

Design notes:
- Demographics (DOB / phone / gender) are CANONICAL per NID and identical across
  every service (hospital, lab, swastha) so the national identity is consistent
  and patient self-activation is predictable.
- Every observation is a multi-point longitudinal SERIES (several dated readings)
  so the cross-hospital trend chart actually draws a line instead of a single dot.
- All writers are IDEMPOTENT (get_or_create keyed on natural keys) so re-running
  `seed` never inserts duplicate rows at the same date.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from clinical import services
from clinical.models import Condition, LocalPatient, Observation

VARIANT = settings.SCHEMA_VARIANT

# Canonical demographics per NID — MUST match lab-service and swastha seeds.
DEMOGRAPHICS = {
    "12345678901": {"name": "Ram Bahadur Thapa", "dob": "1970-05-12", "gender": "MALE", "phone": "9841000001"},
    "12345678902": {"name": "Sita Kumari Sharma", "dob": "1988-11-23", "gender": "FEMALE", "phone": "9803000002"},
    "12345678903": {"name": "Hari Prasad Koirala", "dob": "1979-02-03", "gender": "MALE", "phone": "9841000003"},
}

# Clinical data per org. Observations carry a full dated series (name, value,
# unit, date) so trend lines render across multiple points.
PATIENTS = {
    "HOSP001": [
        {
            "nid": "12345678901",
            "conditions": [("Type 2 Diabetes Mellitus", "E11.9", "2021-06-01")],
            "observations": [
                ("Fasting Blood Glucose", "178", "mg/dL", "2023-01-15"),
                ("Fasting Blood Glucose", "186", "mg/dL", "2023-06-20"),
                ("Fasting Blood Glucose", "190", "mg/dL", "2023-12-05"),
                ("Fasting Blood Glucose", "182", "mg/dL", "2024-01-10"),
                ("Fasting Blood Glucose", "172", "mg/dL", "2024-06-14"),
                ("HbA1c", "7.9", "%", "2023-01-15"),
                ("HbA1c", "8.1", "%", "2023-06-20"),
                ("HbA1c", "8.6", "%", "2023-12-05"),
                ("HbA1c", "8.4", "%", "2024-01-10"),
                ("HbA1c", "7.6", "%", "2024-06-14"),
            ],
        },
        {
            "nid": "12345678902",
            "conditions": [("Essential Hypertension", "I10", "2022-03-15")],
            "observations": [
                ("Blood Pressure Systolic", "142", "mmHg", "2022-03-15"),
                ("Blood Pressure Systolic", "146", "mmHg", "2023-02-10"),
                ("Blood Pressure Systolic", "150", "mmHg", "2023-09-22"),
                ("Blood Pressure Systolic", "148", "mmHg", "2024-02-05"),
                ("Blood Pressure Systolic", "144", "mmHg", "2024-07-18"),
            ],
        },
    ],
    "HOSP002": [
        {
            "nid": "12345678901",
            "conditions": [("Diabetic Nephropathy", "E11.2", "2023-11-20")],
            "observations": [
                ("Serum Creatinine", "1.2", "mg/dL", "2023-11-20"),
                ("Serum Creatinine", "1.6", "mg/dL", "2024-03-01"),
                ("Serum Creatinine", "1.9", "mg/dL", "2024-08-05"),
            ],
        },
        {
            "nid": "12345678903",
            "conditions": [("Ischemic Heart Disease", "I25.9", "2020-08-10")],
            "observations": [
                ("LDL Cholesterol", "158", "mg/dL", "2020-08-10"),
                ("LDL Cholesterol", "165", "mg/dL", "2022-04-15"),
                ("LDL Cholesterol", "170", "mg/dL", "2023-06-10"),
                ("LDL Cholesterol", "162", "mg/dL", "2024-01-22"),
            ],
        },
    ],
}


class Command(BaseCommand):
    help = "Seed demo clinical data for this hospital and index it nationally."

    def handle(self, *args, **options):
        org_code = settings.ORG_CODE
        rows = PATIENTS.get(org_code, [])
        if not rows:
            self.stdout.write(self.style.WARNING(f"No seed data for {org_code}"))
            return

        for row in rows:
            demo = DEMOGRAPHICS[row["nid"]]
            patient = self._make_patient(row["nid"], demo)
            meta = {
                "nid": row["nid"], "full_name": demo["name"],
                "date_of_birth": demo["dob"], "gender": demo["gender"], "phone": demo["phone"],
            }
            for text, code, onset in row.get("conditions", []):
                cond = self._make_condition(patient, text, code, onset)
                status_code, _ = services.push_index(
                    row["nid"], meta, "Condition", cond.id, onset, text)
                self.stdout.write(f"  Condition '{text}' -> index {status_code}")

            for name, value, unit, date in row.get("observations", []):
                obs = self._make_observation(patient, name, value, unit, date)
                status_code, _ = services.push_index(
                    row["nid"], meta, "Observation", obs.id, date, f"{name}: {value} {unit}")
                self.stdout.write(f"  Observation '{name}' @ {date} -> index {status_code}")

        self.stdout.write(self.style.SUCCESS(f"Seeded {settings.ORG_NAME} ({org_code}), variant {VARIANT}."))

    # -- variant-aware writers (all idempotent) ----------------------------
    def _make_patient(self, nid, demo):
        defaults = {"dob": demo["dob"], "gender": demo["gender"], "phone": demo["phone"],
                    "mrn": f"MRN-{nid[-4:]}"}
        if VARIANT == "B":
            parts = demo["name"].split(" ", 1)
            defaults["first_name"] = parts[0]
            defaults["last_name"] = parts[1] if len(parts) > 1 else ""
        else:
            defaults["full_name"] = demo["name"]
        patient, _ = LocalPatient.objects.get_or_create(nid=nid, defaults=defaults)
        return patient

    def _make_condition(self, patient, text, code, onset):
        if VARIANT == "B":
            obj, _ = Condition.objects.get_or_create(
                patient=patient, condition_desc=text, onset=onset,
                defaults={"icd_code": code, "status": "active", "recorded": onset})
            return obj
        obj, _ = Condition.objects.get_or_create(
            patient=patient, diagnosis_text=text, onset_date=onset,
            defaults={"icd10_code": code, "clinical_status": "active", "recorded_date": onset})
        return obj

    def _make_observation(self, patient, name, value, unit, date):
        if VARIANT == "B":
            obj, _ = Observation.objects.get_or_create(
                patient=patient, measurement_name=name, taken_on=date,
                defaults={"measurement_value": value, "measurement_unit": unit})
            return obj
        obj, _ = Observation.objects.get_or_create(
            patient=patient, obs_type=name, observed_date=date,
            defaults={"value": value, "unit": unit})
        return obj
