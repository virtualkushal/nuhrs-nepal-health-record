"""
Seed this lab instance with demo reports and index them nationally.

Uses the SAME shared NIDs as the hospitals so a patient's lab reports appear
alongside their hospital diagnoses in the unified exchange view.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from lab import services
from lab.models import LabPatient, LabReport, LabResult

VARIANT = settings.SCHEMA_VARIANT

# Shared 11-digit Nepal NINs — identical to the hospital seed so a patient's
# lab reports appear alongside their hospital diagnoses in the exchange view.
REPORTS = {
    "LAB001": [
        {"nid": "12345678901", "name": "Ram Bahadur Thapa", "dob": "1975-04-12", "gender": "MALE", "phone": "9841000001",

         "panel": "Lipid Profile", "doctor": "Dr. Sharma", "date": "2024-02-15", "conclusion": "Dyslipidemia",
         "results": [
             {"name": "Total Cholesterol", "value": "245", "unit": "mg/dL", "range": "<200"},
             {"name": "Triglycerides", "value": "210", "unit": "mg/dL", "range": "<150"},
             {"name": "HDL", "value": "38", "unit": "mg/dL", "range": ">40"},
         ]},
        {"nid": "12345678902", "name": "Sita Kumari Sharma", "dob": "1988-09-23", "gender": "FEMALE", "phone": "9841000002",
         "panel": "Complete Blood Count", "doctor": "Dr. Gurung", "date": "2024-02-20", "conclusion": "Mild anemia",
         "results": [
             {"name": "Hemoglobin", "value": "10.5", "unit": "g/dL", "range": "12-16"},
             {"name": "WBC", "value": "7500", "unit": "/uL", "range": "4000-11000"},
         ]},
    ],
    "LAB002": [
        {"nid": "12345678901", "name": "Ram Bahadur Thapa", "dob": "1975-04-12", "gender": "MALE", "phone": "9841000001",
         "panel": "Renal Function Test", "doctor": "Dr. Adhikari", "date": "2024-03-05", "conclusion": "Impaired renal function",
         "results": [
             {"name": "Urea", "value": "58", "unit": "mg/dL", "range": "15-40"},
             {"name": "Creatinine", "value": "1.7", "unit": "mg/dL", "range": "0.6-1.2"},
         ]},
        {"nid": "12345678903", "name": "Hari Prasad Koirala", "dob": "1962-01-30", "gender": "MALE", "phone": "9841000003",
         "panel": "Cardiac Markers", "doctor": "Dr. Rai", "date": "2024-01-25", "conclusion": "Elevated markers",
         "results": [
             {"name": "Troponin I", "value": "0.9", "unit": "ng/mL", "range": "<0.04"},
         ]},
    ],
}


class Command(BaseCommand):
    help = "Seed demo lab reports for this lab and index them nationally."

    def handle(self, *args, **options):
        org_code = settings.ORG_CODE
        rows = REPORTS.get(org_code, [])
        if not rows:
            self.stdout.write(self.style.WARNING(f"No seed data for {org_code}"))
            return

        for row in rows:
            patient = self._make_patient(row)
            report = self._make_report(patient, row)
            for line in row["results"]:
                self._make_result(report, line)

            meta = {"nid": row["nid"], "full_name": row["name"], "date_of_birth": row["dob"],
                    "gender": row["gender"], "phone": row["phone"]}
            status_code, _ = services.push_index(
                row["nid"], meta, "DiagnosticReport", report.id, row["date"], row["panel"])
            self.stdout.write(f"  Report '{row['panel']}' -> index {status_code}")

        self.stdout.write(self.style.SUCCESS(f"Seeded {settings.ORG_NAME} ({org_code}), variant {VARIANT}."))

    def _make_patient(self, row):
        defaults = {"dob": row["dob"], "gender": row["gender"], "phone": row["phone"]}
        if VARIANT == "B":
            parts = row["name"].split(" ", 1)
            defaults["given_name"] = parts[0]
            defaults["surname"] = parts[1] if len(parts) > 1 else ""
        else:
            defaults["patient_name"] = row["name"]
        patient, _ = LabPatient.objects.get_or_create(nid=row["nid"], defaults=defaults)
        return patient

    def _make_report(self, patient, row):
        if VARIANT == "B":
            return LabReport.objects.create(
                patient=patient, test_panel=row["panel"], referred_by=row["doctor"],
                reported_on=row["date"], interpretation=row["conclusion"])
        return LabReport.objects.create(
            patient=patient, panel_name=row["panel"], ordering_doctor=row["doctor"],
            report_date=row["date"], conclusion=row["conclusion"])

    def _make_result(self, report, line):
        if VARIANT == "B":
            return LabResult.objects.create(
                report=report, test_name=line["name"], value=line["value"],
                uom=line["unit"], normal_range=line["range"])
        return LabResult.objects.create(
            report=report, analyte=line["name"], result_value=line["value"],
            units=line["unit"], reference_range=line["range"])
