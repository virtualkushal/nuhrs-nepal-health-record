"""
Seed this hospital instance with demo patients + clinical records, and push each
record's metadata to the National Platform so it becomes discoverable.

The same shared NIDs are used across hospitals/labs so a single patient has a
cross-organization history — this is what makes the exchange demo compelling.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from clinical import services
from clinical.models import Condition, LocalPatient, Observation

VARIANT = settings.SCHEMA_VARIANT

# Shared demo patients — the SAME 11-digit Nepal NIN is used across every
# hospital/lab so one patient has a cross-organization history. These NINs are
# valid by format (11 numeric digits, non-intelligible) per the National
# Identity Card and Registration Act, 2076.
PATIENTS = {
    "HOSP001": [
        {"nid": "12345678901", "name": "Ram Bahadur Thapa", "dob": "1975-04-12", "gender": "MALE", "phone": "9841000001",
         "conditions": [("Type 2 Diabetes Mellitus", "E11.9", "2021-06-01")],
         "observations": [("Fasting Blood Glucose", "182", "mg/dL", "2024-01-10"),
                          ("HbA1c", "8.4", "%", "2024-01-10")]},
        {"nid": "12345678902", "name": "Sita Kumari Sharma", "dob": "1988-09-23", "gender": "FEMALE", "phone": "9841000002",
         "conditions": [("Essential Hypertension", "I10", "2022-03-15")],
         "observations": [("Blood Pressure Systolic", "148", "mmHg", "2024-02-05")]},
    ],
    "HOSP002": [
        {"nid": "12345678901", "name": "Ram Bahadur Thapa", "dob": "1975-04-12", "gender": "MALE", "phone": "9841000001",
         "conditions": [("Diabetic Nephropathy", "E11.2", "2023-11-20")],
         "observations": [("Serum Creatinine", "1.6", "mg/dL", "2024-03-01")]},
        {"nid": "12345678903", "name": "Hari Prasad Koirala", "dob": "1962-01-30", "gender": "MALE", "phone": "9841000003",
         "conditions": [("Ischemic Heart Disease", "I25.9", "2020-08-10")],
         "observations": [("LDL Cholesterol", "162", "mg/dL", "2024-01-22")]},
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
            patient = self._make_patient(row)
            meta = {
                "nid": row["nid"], "full_name": row["name"],
                "date_of_birth": row["dob"], "gender": row["gender"], "phone": row["phone"],
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
                self.stdout.write(f"  Observation '{name}' -> index {status_code}")

        self.stdout.write(self.style.SUCCESS(f"Seeded {settings.ORG_NAME} ({org_code}), variant {VARIANT}."))

    # -- variant-aware writers ---------------------------------------------
    def _make_patient(self, row):
        defaults = {"dob": row["dob"], "gender": row["gender"], "phone": row["phone"],
                    "mrn": f"MRN-{row['nid'][-4:]}"}
        if VARIANT == "B":
            parts = row["name"].split(" ", 1)
            defaults["first_name"] = parts[0]
            defaults["last_name"] = parts[1] if len(parts) > 1 else ""
        else:
            defaults["full_name"] = row["name"]
        patient, _ = LocalPatient.objects.get_or_create(nid=row["nid"], defaults=defaults)
        return patient

    def _make_condition(self, patient, text, code, onset):
        if VARIANT == "B":
            return Condition.objects.create(
                patient=patient, condition_desc=text, icd_code=code, status="active", onset=onset, recorded=onset)
        return Condition.objects.create(
            patient=patient, diagnosis_text=text, icd10_code=code, clinical_status="active",
            onset_date=onset, recorded_date=onset)

    def _make_observation(self, patient, name, value, unit, date):
        if VARIANT == "B":
            return Observation.objects.create(
                patient=patient, measurement_name=name, measurement_value=value,
                measurement_unit=unit, taken_on=date)
        return Observation.objects.create(
            patient=patient, obs_type=name, value=value, unit=unit, observed_date=date)
