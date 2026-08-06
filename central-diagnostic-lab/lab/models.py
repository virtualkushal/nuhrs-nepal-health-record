"""
Laboratory models for Central Diagnostic Laboratory.

Variant A schema (hard-wired): patient_name, panel_name, analyte, result_value,
units, reference_range. The FHIR adapter maps this into standardized
DiagnosticReport + Observation resources with LOINC codes.
"""
from django.db import models


class LabPatient(models.Model):
    nid = models.CharField(max_length=20, db_index=True)
    patient_name = models.CharField(max_length=200)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} [{self.nid}]"


class LabReport(models.Model):
    patient = models.ForeignKey(LabPatient, on_delete=models.CASCADE, related_name="reports")
    panel_name = models.CharField(max_length=200)  # e.g. "Complete Blood Count"
    ordering_doctor = models.CharField(max_length=200, blank=True)
    report_date = models.DateField(null=True, blank=True)
    conclusion = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LabResult(models.Model):
    """A single analyte line within a report."""
    report = models.ForeignKey(LabReport, on_delete=models.CASCADE, related_name="results")
    analyte = models.CharField(max_length=120)
    result_value = models.CharField(max_length=80, blank=True)
    units = models.CharField(max_length=40, blank=True)
    reference_range = models.CharField(max_length=80, blank=True)
