"""
Seed this lab instance with demo reports and index them nationally.

Uses the SAME shared NIDs as the hospitals so a patient's lab reports appear
alongside their hospital diagnoses in the unified exchange view.

Design notes:
- Demographics (DOB / phone / gender) are CANONICAL per NID and identical across
  every service so the national identity is consistent.
- Each panel has multiple dated reports (a series) so the trend view shows
  several points instead of one.
- All writers are IDEMPOTENT (get_or_create on natural keys) so re-running
  `seed` never inserts duplicate rows at the same date.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from lab import services
from lab.models import LabPatient, LabReport, LabResult

VARIANT = settings.SCHEMA_VARIANT

# Canonical demographics per NID — MUST match hospital-service and swastha seeds.
DEMOGRAPHICS = {
    "12345678901": {"name": "Ram Bahadur Thapa", "dob": "1970-05-12", "gender": "MALE", "phone": "9841000001"},
    "12345678902": {"name": "Sita Kumari Sharma", "dob": "1988-11-23", "gender": "FEMALE", "phone": "9803000002"},
    "12345678903": {"name": "Hari Prasad Koirala", "dob": "1979-02-03", "gender": "MALE", "phone": "9841000003"},
}

# Panel definition: name, results, then a list of (date, conclusion) visits.
PANEL_RESULTS = {
    "Lipid Profile": [
        {"name": "Total Cholesterol", "value": "245", "unit": "mg/dL", "range": "<200"},
        {"name": "Triglycerides", "value": "210", "unit": "mg/dL", "range": "<150"},
        {"name": "HDL", "value": "38", "unit": "mg/dL", "range": ">40"},
    ],
    "Complete Blood Count": [
        {"name": "Hemoglobin", "value": "10.5", "unit": "g/dL", "range": "12-16"},
        {"name": "WBC", "value": "7500", "unit": "/uL", "range": "4000-11000"},
    ],
    "Renal Function Test": [
        {"name": "Urea", "value": "58", "unit": "mg/dL", "range": "15-40"},
        {"name": "Creatinine", "value": "1.7", "unit": "mg/dL", "range": "0.6-1.2"},
    ],
    "Cardiac Markers": [
        {"name": "Troponin I", "value": "0.9", "unit": "ng/mL", "range": "<0.04"},
    ],
}

REPORTS = {
    "LAB001": [
        {
            "nid": "12345678901", "panel": "Lipid Profile", "doctor": "Dr. Sharma",
            "visits": [
                ("2023-08-11", "Dyslipidemia"),
                ("2024-02-15", "Dyslipidemia"),
                ("2024-07-22", "Improving lipids"),
            ],
        },
        {
            "nid": "12345678902", "panel": "Complete Blood Count", "doctor": "Dr. Gurung",
            "visits": [
                ("2023-05-30", "Mild anemia"),
                ("2024-02-20", "Mild anemia"),
            ],
        },
    ],
    "LAB002": [
        {
            "nid": "12345678901", "panel": "Renal Function Test", "doctor": "Dr. Adhikari",
            "visits": [
                ("2023-11-20", "Impaired renal function"),
                ("2024-03-05", "Impaired renal function"),
                ("2024-08-05", "Worsening renal function"),
            ],
        },
        {
            "nid": "12345678903", "panel": "Cardiac Markers", "doctor": "Dr. Rai",
            "visits": [
                ("2020-08-10", "Elevated markers"),
                ("2023-06-10", "Elevated markers"),
                ("2024-01-25", "Elevated markers"),
            ],
        },
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
            demo = DEMOGRAPHICS[row["nid"]]
            patient = self._make_patient(row["nid"], demo)
            meta = {"nid": row["nid"], "full_name": demo["name"], "date_of_birth": demo["dob"],
                    "gender": demo["gender"], "phone": demo["phone"]}
            lines = PANEL_RESULTS[row["panel"]]

            for date, conclusion in row["visits"]:
                report = self._make_report(patient, row, date, conclusion)
                for line in lines:
                    self._make_result(report, line)
                status_code, _ = services.push_index(
                    row["nid"], meta, "DiagnosticReport", report.id, date, row["panel"])
                self.stdout.write(f"  Report '{row['panel']}' @ {date} -> index {status_code}")

        self.stdout.write(self.style.SUCCESS(f"Seeded {settings.ORG_NAME} ({org_code}), variant {VARIANT}."))

    def _make_patient(self, nid, demo):
        defaults = {"dob": demo["dob"], "gender": demo["gender"], "phone": demo["phone"]}
        if VARIANT == "B":
            parts = demo["name"].split(" ", 1)
            defaults["given_name"] = parts[0]
            defaults["surname"] = parts[1] if len(parts) > 1 else ""
        else:
            defaults["patient_name"] = demo["name"]
        patient, _ = LabPatient.objects.get_or_create(nid=nid, defaults=defaults)
        return patient

    def _make_report(self, patient, row, date, conclusion):
        if VARIANT == "B":
            obj, _ = LabReport.objects.get_or_create(
                patient=patient, test_panel=row["panel"], reported_on=date,
                defaults={"referred_by": row["doctor"], "interpretation": conclusion})
            return obj
        obj, _ = LabReport.objects.get_or_create(
            patient=patient, panel_name=row["panel"], report_date=date,
            defaults={"ordering_doctor": row["doctor"], "conclusion": conclusion})
        return obj

    def _make_result(self, report, line):
        if VARIANT == "B":
            obj, _ = LabResult.objects.get_or_create(
                report=report, test_name=line["name"],
                defaults={"value": line["value"], "uom": line["unit"], "normal_range": line["range"]})
            return obj
        obj, _ = LabResult.objects.get_or_create(
            report=report, analyte=line["name"],
            defaults={"result_value": line["value"], "units": line["unit"], "reference_range": line["range"]})
        return obj
