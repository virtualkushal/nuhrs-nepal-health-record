"""
Laboratory models for Pathlabs Nepal.

Variant B schema (hard-wired) — DELIBERATELY different column names than Central
Diagnostic Laboratory, to prove the FHIR adapter is schema-agnostic:
  - given_name / surname   (vs Central's single patient_name)
  - test_panel             (vs panel_name)
  - referred_by            (vs ordering_doctor)
  - reported_on            (vs report_date)
  - interpretation         (vs conclusion)
  - test_name / value / uom / normal_range  (vs analyte / result_value / units / reference_range)

Stored in MySQL. The FHIR adapter maps this into the SAME standardized
DiagnosticReport + Observation resources that Central Diagnostic emits.
"""
from django.db import models


class LabPatient(models.Model):
    nid = models.CharField(max_length=20, db_index=True)
    given_name = models.CharField(max_length=120)
    surname = models.CharField(max_length=120, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.given_name} {self.surname} [{self.nid}]"


class LabReport(models.Model):
    patient = models.ForeignKey(
        LabPatient, on_delete=models.CASCADE, related_name="reports")
    test_panel = models.CharField(max_length=200)
    referred_by = models.CharField(max_length=200, blank=True)
    reported_on = models.DateField(null=True, blank=True)
    interpretation = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LabResult(models.Model):
    """A single analyte line within a report."""
    report = models.ForeignKey(
        LabReport, on_delete=models.CASCADE, related_name="results")
    test_name = models.CharField(max_length=120)
    value = models.CharField(max_length=80, blank=True)
    uom = models.CharField(max_length=40, blank=True)
    normal_range = models.CharField(max_length=80, blank=True)
