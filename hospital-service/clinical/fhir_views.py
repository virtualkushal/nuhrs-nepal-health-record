"""FHIR REST endpoints (read-only) exposed to the National Platform."""
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import fhir
from .models import Condition, Encounter, LocalPatient, Observation


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
def patient_everything(request):
    """$everything — return all resources for a patient as one Bundle."""
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    resources = []
    for p in LocalPatient.objects.filter(nid=nid):
        resources.append(fhir.to_fhir_patient(p))
    for e in Encounter.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_encounter(e))
    for c in Condition.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_condition(c))
    for o in Observation.objects.filter(patient__nid=nid):
        resources.append(fhir.to_fhir_observation(o))
    return Response(fhir.make_bundle(resources))
