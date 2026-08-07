"""
FHIR facade for the Mediciti hospital service.

The real mapping logic lives in ``adapter.MedicitiFHIRAdapter``. This module
exposes a simple function-style API (``fhir.to_fhir_patient(p)`` etc.) so the
views and management commands don't need to instantiate the adapter themselves.
"""
from .adapter import MedicitiFHIRAdapter

_adapter = MedicitiFHIRAdapter()


def to_fhir_patient(p):
    return _adapter.to_fhir_patient(p)


def to_fhir_encounter(e):
    return _adapter.to_fhir_encounter(e)


def to_fhir_condition(c):
    return _adapter.to_fhir_condition(c)


def to_fhir_observation(o):
    return _adapter.to_fhir_observation(o)


def to_fhir_allergy(a):
    return _adapter.to_fhir_allergy(a)


def to_fhir_vitals(v):
    return _adapter.to_fhir_vitals(v)


def to_fhir_lab_result(r):
    return _adapter.to_fhir_lab_result(r)


def to_fhir_diagnostic_report(report):
    return _adapter.to_fhir_diagnostic_report(report)


def to_fhir_medication(m):
    return _adapter.to_fhir_medication(m)


def make_bundle(resources):
    return _adapter.make_bundle(resources)


def patient_name(p):
    return _adapter.patient_name(p)
