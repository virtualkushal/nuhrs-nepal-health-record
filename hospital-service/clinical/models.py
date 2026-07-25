"""
Hospital local clinical models.

The "realism trick": Nepal Mediciti (variant A) and Norvic (variant B) store the
SAME clinical facts using DIFFERENT column layouts. To keep one codebase and one
migration set, both variants' columns live here as a superset; each instance only
populates the columns for its configured SCHEMA_VARIANT. The FHIR adapter reads
the correct columns per variant and emits identical FHIR — demonstrating the core
value of HL7 FHIR: heterogeneous local systems, unified standard output.
"""
from django.db import models


class LocalPatient(models.Model):
    nid = models.CharField(max_length=20, db_index=True)

    # Variant A stores a single full_name
    full_name = models.CharField(max_length=200, blank=True)
    # Variant B splits the name
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mrn = models.CharField(max_length=40, blank=True, help_text="Hospital medical record number")
    created_at = models.DateTimeField(auto_now_add=True)

    def display_name(self):
        return self.full_name or f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.display_name()} [{self.nid}]"


class Encounter(models.Model):
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="encounters")

    # Variant A
    doctor_name = models.CharField(max_length=200, blank=True)
    encounter_date = models.DateField(null=True, blank=True)
    encounter_type = models.CharField(max_length=40, blank=True)  # OPD/Emergency/Inpatient
    reason = models.CharField(max_length=255, blank=True)

    # Variant B (different column names)
    physician = models.CharField(max_length=200, blank=True)
    visit_date = models.DateField(null=True, blank=True)
    visit_category = models.CharField(max_length=40, blank=True)
    chief_complaint = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class Condition(models.Model):
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="conditions")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)

    # Variant A
    diagnosis_text = models.CharField(max_length=255, blank=True)
    icd10_code = models.CharField(max_length=20, blank=True)
    clinical_status = models.CharField(max_length=20, blank=True)
    onset_date = models.DateField(null=True, blank=True)
    recorded_date = models.DateField(null=True, blank=True)

    # Variant B (different column names)
    condition_desc = models.CharField(max_length=255, blank=True)
    icd_code = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, blank=True)
    onset = models.DateField(null=True, blank=True)
    recorded = models.DateField(null=True, blank=True)


class Observation(models.Model):
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="observations")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)

    # Variant A
    obs_type = models.CharField(max_length=100, blank=True)
    value = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    observed_date = models.DateField(null=True, blank=True)

    # Variant B
    measurement_name = models.CharField(max_length=100, blank=True)
    measurement_value = models.CharField(max_length=100, blank=True)
    measurement_unit = models.CharField(max_length=40, blank=True)
    taken_on = models.DateField(null=True, blank=True)
