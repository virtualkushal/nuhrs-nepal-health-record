"""
Seed Central Diagnostic Laboratory with comprehensive demo reports.

Uses the shared NIDs (12345678901, 02, 03) so reports merge into the unified
exchange. Demographics are CANONICAL per NID. Each panel gets multiple dated
reports (a series) for trend visualization.

All writers are IDEMPOTENT (get_or_create on natural keys) so re-running never
inserts duplicate rows at the same date.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from lab import catalog, services
from lab.models import LabPatient, LabReport, LabResult

ORG_CODE = settings.ORG_CODE

# Canonical demographics per NID — MUST match the hospital and swastha seeds.
DEMOGRAPHICS = {
    "12345678901": {"name": "Ram Bahadur Thapa", "dob": "1970-05-12", "gender": "MALE", "phone": "9841000001"},
    "12345678902": {"name": "Sita Kumari Sharma", "dob": "1988-11-23", "gender": "FEMALE", "phone": "9803000002"},
    "12345678903": {"name": "Hari Prasad Koirala", "dob": "1979-02-03", "gender": "MALE", "phone": "9841000003"},
}

# Central Diagnostic (LAB001) comprehensive test menu: distribute panels across
# the three patients with multiple dated visits per panel (series for trends).
REPORTS_LAB001 = [
    # Ram Bahadur (NID 01) — Lipid Profile + Diabetic Profile + LFT
    {
        "nid": "12345678901", "panel": "Lipid Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-08-11", "Dyslipidemia", {
                "Total Cholesterol": "245", "LDL Cholesterol": "165", "HDL Cholesterol": "38", "Triglycerides": "210"}),
            ("2024-02-15", "Dyslipidemia", {
                "Total Cholesterol": "235", "LDL Cholesterol": "155", "HDL Cholesterol": "40", "Triglycerides": "200"}),
            ("2024-07-22", "Improving lipids", {
                "Total Cholesterol": "205", "LDL Cholesterol": "125", "HDL Cholesterol": "45", "Triglycerides": "175"}),
        ],
    },
    {
        "nid": "12345678901", "panel": "Diabetic Profile", "doctor": "Dr. Sharma",
        "visits": [
            ("2023-09-10", "Impaired fasting glucose", {
                "Fasting Blood Sugar": "115", "Postprandial Blood Sugar": "165", "HbA1c": "6.2"}),
            ("2024-03-05", "Pre-diabetes", {
                "Fasting Blood Sugar": "108", "Postprandial Blood Sugar": "155", "HbA1c": "5.9"}),
        ],
    },
    {
        "nid": "12345678901", "panel": "Liver Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2024-01-20", "Mildly elevated transaminases", {
                "Total Bilirubin": "0.9", "Direct Bilirubin": "0.2", "SGPT / ALT": "68", "SGOT / AST": "55",
                "Alkaline Phosphatase": "95", "Total Protein": "7.1", "Albumin": "4.2"}),
        ],
    },
    
    # Sita Kumari (NID 02) — CBC + Thyroid + Iron Studies
    {
        "nid": "12345678902", "panel": "Complete Blood Count", "doctor": "Dr. Gurung",
        "visits": [
            ("2023-05-30", "Mild anemia", {
                "Hemoglobin": "10.5", "Total RBC Count": "4.0", "Total WBC Count": "7500", "Platelet Count": "280",
                "Hematocrit": "33", "MCV": "82", "MCH": "28", "MCHC": "32"}),
            ("2024-02-20", "Mild anemia", {
                "Hemoglobin": "10.8", "Total RBC Count": "4.1", "Total WBC Count": "7200", "Platelet Count": "295",
                "Hematocrit": "34", "MCV": "83", "MCH": "28", "MCHC": "32"}),
            ("2024-08-01", "Improving hemoglobin", {
                "Hemoglobin": "11.4", "Total RBC Count": "4.3", "Total WBC Count": "7800", "Platelet Count": "310",
                "Hematocrit": "36", "MCV": "84", "MCH": "29", "MCHC": "32"}),
        ],
    },
    {
        "nid": "12345678902", "panel": "Thyroid Function Test", "doctor": "Dr. Paudel",
        "visits": [
            ("2023-11-15", "Subclinical hypothyroidism", {
                "TSH": "6.2", "Free T3": "2.8", "Free T4": "0.9"}),
            ("2024-05-10", "Normal on treatment", {
                "TSH": "2.1", "Free T3": "3.1", "Free T4": "1.2"}),
        ],
    },
    {
        "nid": "12345678902", "panel": "Iron Studies", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-03-01", "Iron deficiency", {
                "Serum Iron": "45", "Ferritin": "18", "TIBC": "420"}),
        ],
    },
    
    # Hari Prasad (NID 03) — Cardiac Markers + Electrolyte + Vitamin Assay + Febrile Illness
    {
        "nid": "12345678903", "panel": "Cardiac Markers", "doctor": "Dr. Rai",
        "visits": [
            ("2020-08-10", "Elevated markers", {
                "Troponin I": "0.9", "CK-MB": "8.5", "D-Dimer": "620"}),
            ("2023-06-10", "Elevated markers", {
                "Troponin I": "0.06", "CK-MB": "4.2", "D-Dimer": "580"}),
            ("2024-01-25", "Elevated D-Dimer", {
                "Troponin I": "0.03", "CK-MB": "3.8", "D-Dimer": "820"}),
        ],
    },
    {
        "nid": "12345678903", "panel": "Electrolyte Panel", "doctor": "Dr. Rai",
        "visits": [
            ("2024-02-10", "Mild hypokalemia", {
                "Sodium": "138", "Potassium": "3.3", "Chloride": "102", "Calcium": "9.2"}),
        ],
    },
    {
        "nid": "12345678903", "panel": "Vitamin Assay", "doctor": "Dr. Thapa",
        "visits": [
            ("2024-04-15", "Vitamin D deficiency", {
                "Vitamin D (25-OH)": "18", "Vitamin B12": "320"}),
        ],
    },
    {
        "nid": "12345678903", "panel": "Febrile Illness Panel", "doctor": "Dr. Joshi",
        "visits": [
            ("2024-08-05", "Scrub typhus suspected", {
                "Widal Test": "Negative", "Typhidot IgM": "Negative", "Dengue NS1 Antigen": "Negative",
                "Dengue IgM": "Negative", "Malaria Antigen": "Negative", "Scrub Typhus IgM": "POSITIVE (ELISA)",
                "C-Reactive Protein": "45"}),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed Central Diagnostic Laboratory with comprehensive demo reports."

    def handle(self, *args, **options):
        if ORG_CODE != "LAB001":
            self.stdout.write(self.style.WARNING(f"This seed is for LAB001, not {ORG_CODE}"))
            return

        for row in REPORTS_LAB001:
            demo = DEMOGRAPHICS[row["nid"]]
            patient = self._make_patient(row["nid"], demo)
            meta = {"nid": row["nid"], "full_name": demo["name"], "date_of_birth": demo["dob"],
                    "gender": demo["gender"], "phone": demo["phone"]}
            panel_name = row["panel"]

            for date, conclusion, values_dict in row["visits"]:
                report = self._make_report(patient, panel_name, row["doctor"], date, conclusion)
                for analyte_name, value_str in values_dict.items():
                    self._make_result(report, analyte_name, value_str)
                status_code, _ = services.push_index(
                    row["nid"], meta, "DiagnosticReport", report.id, date, panel_name)
                self.stdout.write(f"  {panel_name} @ {date} -> index {status_code}")

        self.stdout.write(self.style.SUCCESS(f"Seeded {settings.ORG_NAME} ({ORG_CODE})."))

    def _make_patient(self, nid, demo):
        defaults = {"dob": demo["dob"], "gender": demo["gender"], "phone": demo["phone"],
                    "patient_name": demo["name"]}
        patient, _ = LabPatient.objects.get_or_create(nid=nid, defaults=defaults)
        return patient

    def _make_report(self, patient, panel_name, doctor, date, conclusion):
        obj, _ = LabReport.objects.get_or_create(
            patient=patient, panel_name=panel_name, report_date=date,
            defaults={"ordering_doctor": doctor, "conclusion": conclusion})
        return obj

    def _make_result(self, report, analyte_name, value_str):
        meta = catalog.analyte_meta(analyte_name)
        unit = meta.get("unit", "")
        range_low = meta.get("low")
        range_high = meta.get("high")
        if range_low is not None and range_high is not None:
            range_str = f"{range_low}-{range_high}"
        elif range_low is not None:
            range_str = f">{range_low}"
        elif range_high is not None:
            range_str = f"<{range_high}"
        else:
            range_str = ""
        
        obj, _ = LabResult.objects.get_or_create(
            report=report, analyte=analyte_name,
            defaults={"result_value": value_str, "units": unit, "reference_range": range_str})
        return obj
