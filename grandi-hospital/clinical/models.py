"""
Norvic International Hospital — local clinical database models ("variant B").

This is Norvic's OWN schema. It stores the SAME clinical facts as Nepal Mediciti
but under DIFFERENT column names — reflecting the reality that two hospitals
running different HMIS vendors design their databases differently:

    Fact              Mediciti (variant A)   Norvic (variant B, this file)
    ----------------  ---------------------  -----------------------------
    Patient name      full_name              first_name + last_name
    Clinician         doctor_name            physician
    Visit date        encounter_date         visit_date
    Visit type        encounter_type         visit_category
    Visit reason      reason                 chief_complaint
    Diagnosis text    diagnosis_text         condition_desc
    ICD code          icd10_code             icd_code
    Condition status  clinical_status        status
    Onset date        onset_date             onset
    Observation name  obs_type               measurement_name
    Observation value value                  measurement_value
    Observation unit  unit                   measurement_unit
    Observation date  observed_date          taken_on

Norvic ALSO offers services Mediciti does not — Immunization (vaccination
records) and Procedure (surgical/cardiac procedures) — modeled at the bottom.

Each hospital's FHIR adapter translates these local columns into byte-for-byte
identical HL7 FHIR R4. That translation is the whole point of the standard.
"""
from django.db import models


class LocalPatient(models.Model):
    nid = models.CharField(max_length=20, db_index=True)

    # Variant B: name stored as two columns instead of one full_name.
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mrn = models.CharField(max_length=40, blank=True, help_text="Hospital medical record number")

    # Rich registration demographics — makes the DB look like a real hospital record.
    address = models.CharField(max_length=255, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)  # e.g. O+, AB-
    marital_status = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    ethnicity = models.CharField(max_length=100, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def display_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.display_name()} [{self.nid}]"


class Encounter(models.Model):
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="encounters")

    # Variant B column names.
    physician = models.CharField(max_length=200, blank=True)
    visit_date = models.DateField(null=True, blank=True)
    visit_category = models.CharField(max_length=40, blank=True)  # OPD/Emergency/Inpatient
    chief_complaint = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=120, blank=True)  # e.g. Cardiology, CTVS
    ward = models.CharField(max_length=60, blank=True)  # for inpatient stays

    created_at = models.DateTimeField(auto_now_add=True)


class Condition(models.Model):
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="conditions")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)

    # Variant B column names.
    condition_desc = models.CharField(max_length=255, blank=True)
    icd_code = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, blank=True)
    onset = models.DateField(null=True, blank=True)
    recorded = models.DateField(null=True, blank=True)


class Observation(models.Model):
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="observations")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)

    # Variant B column names.
    measurement_name = models.CharField(max_length=100, blank=True)
    measurement_value = models.CharField(max_length=100, blank=True)
    measurement_unit = models.CharField(max_length=40, blank=True)
    taken_on = models.DateField(null=True, blank=True)


# ---------------------------------------------------------------------------
# Shared hospital features (same column names as Mediciti — these tables were
# added later, after both hospitals adopted a common convention for them).
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


# ---------------------------------------------------------------------------
# Norvic-ONLY services (Mediciti does not offer these)
# ---------------------------------------------------------------------------


class Immunization(models.Model):
    """
    Vaccination record. Norvic runs a travel & routine immunization clinic that
    Mediciti (in this demo) does not — so this whole resource type only appears
    in the national record when Norvic is one of the patient's providers.
    """
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="immunizations")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)

    vaccine_name = models.CharField(max_length=200)  # e.g. COVID-19 (Covishield), Hepatitis B
    cvx_code = models.CharField(max_length=20, blank=True)  # CDC CVX vaccine code
    dose_number = models.CharField(max_length=20, blank=True)  # e.g. 1, 2, Booster
    lot_number = models.CharField(max_length=40, blank=True)
    site = models.CharField(max_length=60, blank=True)  # e.g. Left deltoid
    route = models.CharField(max_length=40, blank=True)  # e.g. Intramuscular
    administered_date = models.DateField(null=True, blank=True)
    administered_by = models.CharField(max_length=200, blank=True)


class Procedure(models.Model):
    """
    Surgical / interventional procedure. Norvic is a cardiac-surgery centre, so
    it records Procedures (CABG, angioplasty, valve replacement ...) that a
    general hospital may not — another service Mediciti lacks in this demo.
    """
    patient = models.ForeignKey(LocalPatient, on_delete=models.CASCADE, related_name="procedures")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL)

    procedure_name = models.CharField(max_length=255)  # e.g. Coronary Artery Bypass Grafting
    snomed_code = models.CharField(max_length=20, blank=True)  # SNOMED CT procedure code
    category = models.CharField(max_length=100, blank=True)  # e.g. Cardiac Surgery
    performed_date = models.DateField(null=True, blank=True)
    surgeon = models.CharField(max_length=200, blank=True)
    outcome = models.CharField(max_length=255, blank=True)  # e.g. Successful, No complications
    notes = models.TextField(blank=True)


