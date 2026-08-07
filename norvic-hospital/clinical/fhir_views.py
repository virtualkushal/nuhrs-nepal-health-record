"""FHIR REST endpoints (read-only) exposed to the National Platform."""
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import fhir
from .models import (
    Allergy,
    Condition,
    Encounter,
    Immunization,
    LabReport,
    LabResult,
    LocalPatient,
    MedicationRequest,
    Observation,
    Procedure,
    Vitals,
)


def _check_api_key(request):
    return request.headers.get("X-API-Key") == settings.ORG_API_KEY


def _unauthorized():
    return Response({"detail": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["GET"])
def patient_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("identifier") or request.query_params.get("patient")
    patients = LocalPatient.objects.filter(nid=nid)
    return Response(fhir.make_bundle([fhir.to_fhir_patient(p) for p in patients]))


@api_view(["GET"])
def encounter_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = Encounter.objects.filter(patient__nid=nid)
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(fhir.make_bundle([fhir.to_fhir_encounter(e) for e in qs]))


@api_view(["GET"])
def condition_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = Condition.objects.filter(patient__nid=nid)
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(fhir.make_bundle([fhir.to_fhir_condition(c) for c in qs]))


@api_view(["GET"])
def observation_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = Observation.objects.filter(patient__nid=nid)
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(fhir.make_bundle([fhir.to_fhir_observation(o) for o in qs]))


@api_view(["GET"])
def allergy_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = Allergy.objects.filter(patient__nid=nid)
    return Response(fhir.make_bundle([fhir.to_fhir_allergy(a) for a in qs]))


@api_view(["GET"])
def medication_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = MedicationRequest.objects.filter(patient__nid=nid)
    return Response(fhir.make_bundle([fhir.to_fhir_medication(m) for m in qs]))


@api_view(["GET"])
def diagnostic_report_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = LabReport.objects.filter(patient__nid=nid)
    return Response(fhir.make_bundle([fhir.to_fhir_diagnostic_report(r) for r in qs]))


@api_view(["GET"])
def immunization_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = Immunization.objects.filter(patient__nid=nid)
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(fhir.make_bundle([fhir.to_fhir_immunization(i) for i in qs]))


@api_view(["GET"])
def procedure_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = Procedure.objects.filter(patient__nid=nid)
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(fhir.make_bundle([fhir.to_fhir_procedure(p) for p in qs]))


def _all_resources_for(nid):
    """Collect every FHIR resource for a patient (used by $everything)."""
    resources = []
    for p in LocalPatient.objects.filter(nid=nid):
        resources.append(fhir.to_fhir_patient(p))
    for a in Allergy.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_allergy(a))
    for e in Encounter.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_encounter(e))
    for c in Condition.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_condition(c))
    # Legacy free-form observations
    for o in Observation.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_observation(o))
    # Vitals -> one Observation per measurement
    for v in Vitals.objects.filter(patient__nid=nid):
        resources.extend(fhir.to_fhir_vitals(v))
    # Lab reports (DiagnosticReport) + their analyte Observations
    for report in LabReport.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_diagnostic_report(report))
    for res in LabResult.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_lab_result(res))
    # Medications
    for m in MedicationRequest.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_medication(m))
    # Norvic-only: Immunizations + Procedures
    for imm in Immunization.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_immunization(imm))
    for proc in Procedure.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_procedure(proc))
    return resources


@api_view(["GET"])
def patient_everything(request):
    """$everything — return all resources for a patient as one Bundle."""
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    return Response(fhir.make_bundle(_all_resources_for(nid)))
