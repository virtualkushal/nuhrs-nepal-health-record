"""
MedicitiFHIRAdapter — Nepal Mediciti Hospital (schema variant A).

Mediciti's HMIS stores clinical facts using variant-A column names
(``full_name``, ``diagnosis_text``, ``icd10_code``, ``obs_type`` ...). This
adapter reads those columns and hands them to the shared FHIR builders in
``BaseFHIRAdapter``.
"""
from .base_adapter import BaseFHIRAdapter


class MedicitiFHIRAdapter(BaseFHIRAdapter):
    """Concrete FHIR adapter for Nepal Mediciti Hospital (variant A)."""

    def patient_name(self, p):
        return p.full_name

    def encounter_fields(self, e):
        return {
            "clinician": e.doctor_name,
            "date": e.encounter_date,
            "category": e.encounter_type,
            "reason": e.reason,
        }

    def condition_fields(self, c):
        return {
            "text": c.diagnosis_text,
            "code": c.icd10_code,
            "status": c.clinical_status,
            "onset": c.onset_date,
        }

    def observation_fields(self, o):
        return {
            "name": o.obs_type,
            "value": o.value,
            "unit": o.unit,
            "date": o.observed_date,
        }
