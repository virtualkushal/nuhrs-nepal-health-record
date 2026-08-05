"""
Backward-compatible FHIR facade.

The real logic now lives in the ``adapters`` package as named, per-hospital
classes (MedicitiFHIRAdapter, NorvicFHIRAdapter). This module keeps the old
function-style API (``fhir.to_fhir_patient(p)`` etc.) working by delegating to
the adapter selected for this hospital instance via ``get_adapter()``.
"""
from .adapters import get_adapter

_adapter = get_adapter()


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


