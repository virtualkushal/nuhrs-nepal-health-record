"""
Laboratory local models.

Like the hospital service, two schema variants (A = Central Diagnostic Lab,
B = Pathlabs Nepal) store the same lab-report facts with different column names.
The FHIR adapter maps both into identical DiagnosticReport + Observation output.
"""
from django.db import models


class LabPatient(models.Model):
    nid = models.CharField(max_length=20, db_index=True)

    # Variant A
    patient_name = models.CharField(max_length=200, blank=True)
    # Variant B
    given_name = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)

    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def display_name(self):
        return self.patient_name or f"{self.given_name} {self.surname}".strip()

    def __str__(self):
        return f"{self.display_name()} [{self.nid}]"


class LabReport(models.Model):
    patient = models.ForeignKey(LabPatient, on_delete=models.CASCADE, related_name="reports")

    # Variant A
    panel_name = models.CharField(max_length=200, blank=True)  # e.g. "Lipid Profile"
    ordering_doctor = models.CharField(max_length=200, blank=True)
    report_date = models.DateField(null=True, blank=True)
    conclusion = models.CharField(max_length=255, blank=True)

    # Variant B (different column names)
    test_panel = models.CharField(max_length=200, blank=True)
    referred_by = models.CharField(max_length=200, blank=True)
    reported_on = models.DateField(null=True, blank=True)
    interpretation = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class LabResult(models.Model):
    """A single analyte line within a report."""

    report = models.ForeignKey(LabReport, on_delete=models.CASCADE, related_name="results")

    # Variant A
    analyte = models.CharField(max_length=120, blank=True)
    result_value = models.CharField(max_length=80, blank=True)
    units = models.CharField(max_length=40, blank=True)
    reference_range = models.CharField(max_length=80, blank=True)

    # Variant B
    test_name = models.CharField(max_length=120, blank=True)
    value = models.CharField(max_length=80, blank=True)
    uom = models.CharField(max_length=40, blank=True)
    normal_range = models.CharField(max_length=80, blank=True)
