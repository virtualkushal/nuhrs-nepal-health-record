"""
Seed Pathlabs Nepal with comprehensive demo reports.

Uses the shared NIDs (2345678901, 02, 03) so reports merge into the unified
exchange. Demographics are CANONICAL per NID. Each panel gets multiple dated
reports (a series) for trend visualization.

All writers are IDEMPOTENT (get_or_create on natural keys) so re-running never
inserts duplicate rows at the same date.

Pathlabs Nepal (LAB002, variant B schema, MySQL) gets different panels than
Central Diagnostic (LAB001) to demonstrate specialization + federation.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from lab import catalog, services
from lab.models import LabPatient, LabReport, LabResult

ORG_CODE = settings.ORG_CODE

# Canonical demographics per NID — MUST match the hospital and swastha seeds.
DEMOGRAPHICS = {
    "2345678901": {"name": "Ram Bahadur Thapa", "dob": "1970-05-12", "gender": "MALE", "phone": "9841000001"},
    "2345678902": {"name": "Sita Kumari Sharma", "dob": "1988-11-23", "gender": "FEMALE", "phone": "9803000002"},
    "2345678903": {"name": "Hari Prasad Koirala", "dob": "1979-02-03", "gender": "MALE", "phone": "9841000003"},
    # Cross-facility demo patients — match Mediciti / Norvic / Central Diagnostic seeds.
    "2345678909": {"name": "Laxmi Maya Tamang", "dob": "1993-04-14", "gender": "FEMALE", "phone": "9842000001"},
    "2345678910": {"name": "Kiran Bahadur Limbu", "dob": "1985-09-19", "gender": "MALE", "phone": "9842000002"},
}

# Pathlabs Nepal (LAB002) comprehensive test menu: DIFFERENT panels than Central
# Diagnostic to show lab specialization in the federated system.
REPORTS_LAB002 = [
    # Ram Bahadur (NID 01) — Renal Function + Coagulation + Viral Markers
    {
        "nid": "2345678901", "panel": "Renal Function Test", "doctor": "Dr. Adhikari",
        "visits": [
            ("2023-11-20", "Impaired renal function", {
                "Urea": "58", "Blood Urea Nitrogen": "27", "Creatinine": "1.7", "Uric Acid": "8.5"}),
            ("2024-03-05", "Impaired renal function", {
                "Urea": "62", "Blood Urea Nitrogen": "29", "Creatinine": "1.8", "Uric Acid": "8.8"}),
            ("2024-08-05", "Worsening renal function", {
                "Urea": "75", "Blood Urea Nitrogen": "35", "Creatinine": "2.1", "Uric Acid": "9.2"}),
        ],
    },
    {
        "nid": "2345678901", "panel": "Coagulation Profile", "doctor": "Dr. Rai",
        "visits": [
            ("2024-02-10", "Prolonged PT", {
                "Prothrombin Time": "15.2", "INR": "1.4", "aPTT": "32"}),
        ],
    },
    {
        "nid": "2345678901", "panel": "Viral Markers", "doctor": "Dr. Joshi",
        "visits": [
            ("2024-06-15", "Negative for viral hepatitis and HIV", {
                "HBsAg": "NEGATIVE", "Anti-HCV": "NEGATIVE", "HIV I/II": "NEGATIVE", "VDRL": "Non-reactive"}),
        ],
    },
    
    # Sita Kumari (NID 02) — Electrolytes + Urine + Stool
    {
        "nid": "2345678902", "panel": "Electrolyte Panel", "doctor": "Dr. Paudel",
        "visits": [
            ("2023-09-20", "Mild hyponatremia", {
                "Sodium": "132", "Potassium": "4.2", "Chloride": "98", "Calcium": "8.8"}),
            ("2024-04-10", "Normal electrolytes", {
                "Sodium": "138", "Potassium": "4.0", "Chloride": "102", "Calcium": "9.2"}),
        ],
    },
    {
        "nid": "2345678902", "panel": "Urine Routine Examination", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-03-15", "Mild proteinuria", {
                "Urine Routine & Microscopy": "Protein 1+, RBC 2-3/hpf, WBC occasional"}),
        ],
    },
    {
        "nid": "2345678902", "panel": "Stool Examination", "doctor": "Dr. Thapa",
        "visits": [
            ("2024-07-10", "Normal stool", {
                "Stool Routine & Microscopy": "No ova/cysts seen, no RBC/WBC", "Culture & Sensitivity": "No pathogen isolated"}),
        ],
    },
    
    # Hari Prasad (NID 03) — CBC (for comparison with Central) + Febrile + Vitamin
    {
        "nid": "2345678903", "panel": "Complete Blood Count", "doctor": "Dr. Sharma",
        "visits": [
            ("2024-01-15", "Mild leukocytosis", {
                "Hemoglobin": "14.2", "Total RBC Count": "4.8", "Total WBC Count": "12500", "Platelet Count": "320",
                "Hematocrit": "42", "MCV": "88", "MCH": "30", "MCHC": "34"}),
        ],
    },
    {
        "nid": "2345678903", "panel": "Febrile Illness Panel", "doctor": "Dr. Adhikari",
        "visits": [
            ("2024-07-25", "Dengue IgM positive", {
                "Widal Test": "Negative", "Typhidot IgM": "Negative", "Dengue NS1 Antigen": "POSITIVE",
                "Dengue IgM": "POSITIVE (ELISA)", "Malaria Antigen": "Negative", "Scrub Typhus IgM": "Negative",
                "C-Reactive Protein": "38"}),
        ],
    },
    {
        "nid": "2345678903", "panel": "Vitamin Assay", "doctor": "Dr. Rai",
        "visits": [
            ("2024-05-20", "Low Vitamin D", {
                "Vitamin D (25-OH)": "22", "Vitamin B12": "450"}),
        ],
    },

    # Laxmi Maya (NID 09) — routine wellness panels at Pathlabs
    {
        "nid": "2345678909", "panel": "Electrolyte Panel", "doctor": "Dr. Paudel",
        "visits": [
            ("2023-11-08", "Normal electrolytes", {
                "Sodium": "139", "Potassium": "4.0", "Chloride": "101", "Calcium": "9.4"}),
            ("2024-07-06", "Normal electrolytes", {
                "Sodium": "140", "Potassium": "4.1", "Chloride": "103", "Calcium": "9.6"}),
        ],
    },
    {
        "nid": "2345678909", "panel": "Urine Routine Examination", "doctor": "Dr. Gurung",
        "visits": [
            ("2024-02-14", "Unremarkable", {
                "Urine Routine & Microscopy": "Clear, no protein, no cells seen"}),
        ],
    },
    {
        "nid": "2345678909", "panel": "Vitamin Assay", "doctor": "Dr. Thapa",
        "visits": [
            ("2024-01-30", "Normal vitamin levels", {
                "Vitamin D (25-OH)": "38", "Vitamin B12": "520"}),
        ],
    },

    # Kiran Bahadur (NID 10) — pre-procedure screening + CBC follow-up
    {
        "nid": "2345678910", "panel": "Complete Blood Count", "doctor": "Dr. Sharma",
        "visits": [
            ("2024-05-16", "Normal, mild leukocytosis", {
                "Hemoglobin": "15.1", "Total RBC Count": "5.0", "Total WBC Count": "11800", "Platelet Count": "300",
                "Hematocrit": "46", "MCV": "90", "MCH": "30", "MCHC": "33"}),
        ],
    },
    {
        "nid": "2345678910", "panel": "Viral Markers", "doctor": "Dr. Joshi",
        "visits": [
            ("2024-07-01", "Negative screen", {
                "HBsAg": "NEGATIVE", "Anti-HCV": "NEGATIVE", "HIV I/II": "NEGATIVE", "VDRL": "Non-reactive"}),
        ],
    },
    {
        "nid": "2345678910", "panel": "Coagulation Profile", "doctor": "Dr. Rai",
        "visits": [
            ("2024-07-05", "Normal coagulation", {
                "Prothrombin Time": "12.1", "INR": "1.0", "aPTT": "31"}),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed Pathlabs Nepal with comprehensive demo reports."

    def handle(self, *args, **options):
        if ORG_CODE != "LAB002":
            self.stdout.write(self.style.WARNING(f"This seed is for LAB002, not {ORG_CODE}"))
            return

        for row in REPORTS_LAB002:
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
        parts = demo["name"].split(" ", 1)
        defaults = {"dob": demo["dob"], "gender": demo["gender"], "phone": demo["phone"],
                    "given_name": parts[0], "surname": parts[1] if len(parts) > 1 else ""}
        patient, _ = LabPatient.objects.get_or_create(nid=nid, defaults=defaults)
        return patient

    def _make_report(self, patient, panel_name, doctor, date, conclusion):
        obj, _ = LabReport.objects.get_or_create(
            patient=patient, test_panel=panel_name, reported_on=date,
            defaults={"referred_by": doctor, "interpretation": conclusion})
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
            report=report, test_name=analyte_name,
            defaults={"value": value_str, "uom": unit, "normal_range": range_str})
        return obj
