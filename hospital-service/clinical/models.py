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

    # Rich demographics (Mediciti / variant A) — make the DB look like a real
    # hospital registration record.
    address = models.CharField(max_length=255, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)  # e.g. O+, AB-
    marital_status = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    ethnicity = models.CharField(max_length=100, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)

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
    department = models.CharField(max_length=120, blank=True)  # e.g. Cardiology, Nephrology
    ward = models.CharField(max_length=60, blank=True)  # for inpatient stays


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


# ---------------------------------------------------------------------------
# NEW MODELS — realistic hospital features (Mediciti, variant A primarily)
# ---------------------------------------------------------------------------


class Vitals(models.Model):
    """Nurse-recorded vital signs at each encounter — real hospital behavior."""
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="vitals")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)
    recorded_date = models.DateTimeField(auto_now_add=True)

    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)
    pulse = models.IntegerField(null=True, blank=True)  # bpm
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)  # Celsius
    spo2 = models.IntegerField(null=True, blank=True)  # oxygen saturation %
    respiratory_rate = models.IntegerField(null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Vitals"


class Allergy(models.Model):
    """Patient allergies — critical safety information."""
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="allergies")
    allergen = models.CharField(max_length=200)  # e.g. Penicillin, Peanuts
    reaction = models.CharField(max_length=255, blank=True)  # e.g. Rash, Anaphylaxis
    severity = models.CharField(max_length=20, blank=True)  # mild/moderate/severe
    recorded_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Allergies"


class LabOrder(models.Model):
    """Doctor orders a lab test/panel (the requisition)."""
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="lab_orders")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)
    ordering_doctor = models.CharField(max_length=200, blank=True)
    panel_name = models.CharField(max_length=150)  # e.g. Complete Blood Count, Lipid Profile
    ordered_date = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=20, blank=True)  # routine/urgent/stat


class LabReport(models.Model):
    """The lab produces one report per ordered panel, containing multiple results."""
    order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name="report")
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="lab_reports")
    panel_name = models.CharField(max_length=150)
    report_date = models.DateField()
    status = models.CharField(max_length=20, default="final")  # preliminary/final/corrected


class LabResult(models.Model):
    """Individual analyte result inside a lab report (LOINC-coded)."""
    report = models.ForeignKey(LabReport, on_delete=models.CASCADE, related_name="results")
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="lab_results")

    test_name = models.CharField(max_length=200)  # e.g. Hemoglobin, Total Cholesterol
    loinc_code = models.CharField(max_length=20, blank=True)
    value = models.CharField(max_length=50)
    unit = models.CharField(max_length=30, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)  # e.g. 13.5-17.5 g/dL
    interpretation = models.CharField(max_length=10, blank=True)  # H (high), L (low), N (normal)

    class Meta:
        verbose_name_plural = "Lab Results"


class MedicationRequest(models.Model):
    """Prescription — what drug, dose, frequency the doctor ordered."""
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="medications")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)

    medication_name = models.CharField(max_length=200)  # e.g. Metformin
    rxnorm_code = models.CharField(max_length=20, blank=True)
    dosage = models.CharField(max_length=100)  # e.g. 500 mg
    frequency = models.CharField(max_length=100)  # e.g. twice daily, BID
    route = models.CharField(max_length=50, blank=True)  # oral/IV/topical
    duration = models.CharField(max_length=100, blank=True)  # e.g. 30 days, ongoing
    prescribed_date = models.DateField()
    prescriber = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Medication Request"
        verbose_name_plural = "Medication Requests"


