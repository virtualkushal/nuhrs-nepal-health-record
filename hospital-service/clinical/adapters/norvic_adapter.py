"""
NorvicFHIRAdapter — Norvic International Hospital (schema variant B).

Norvic's EHR stores the SAME clinical facts using different column names
(``first_name``/``last_name``, ``condition_desc``, ``icd_code``,
``measurement_name`` ...). This adapter reads those columns and hands them to
the shared FHIR builders in ``BaseFHIRAdapter`` — producing FHIR identical to
Mediciti's, which is the whole point of the standard.
"""
from .base_adapter import BaseFHIRAdapter


class NorvicFHIRAdapter(BaseFHIRAdapter):
    """Concrete FHIR adapter for Norvic International Hospital (variant B)."""

    def patient_name(self, p):
        return f"{p.first_name} {p.last_name}".strip()

    def encounter_fields(self, e):
        return {
            "clinician": e.physician,
            "date": e.visit_date,
            "category": e.visit_category,
            "reason": e.chief_complaint,
        }

    def condition_fields(self, c):
        return {
            "text": c.condition_desc,
            "code": c.icd_code,
            "status": c.status,
            "onset": c.onset,
        }

    def observation_fields(self, o):
        return {
            "name": o.measurement_name,
            "value": o.measurement_value,
            "unit": o.measurement_unit,
            "date": o.taken_on,
        }
