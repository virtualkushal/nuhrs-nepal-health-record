"""
NUHRS federation adapter for SwasthyaEHR.

The National Platform's RoutingEngine discovers a patient's records via the
metadata index, then fetches the real clinical data from each owning org by
calling that org's FHIR adapter, keyed by National ID (NID) and guarded by an
X-API-Key header:

    GET {api_base_url}/$everything?patient={nid}
    GET {api_base_url}/{ResourceType}?patient={nid}&_id={local_id}

`api_base_url` for this instance is registered on the platform as
`http://<host>/fhir`, so every route below is mounted under /fhir/.

These endpoints are NID-keyed (unlike core.views' UUID-keyed FHIR layer) and
reuse the hand-built FHIR R4 serializers in fhir_serializers so the emitted
resources stay identical across both layers.
"""

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .fhir_serializers import (
    condition_to_fhir,
    encounter_to_fhir,
    medicationrequest_to_fhir,
    observation_to_fhir,
    patient_to_fhir,
)
from .models import Diagnosis, Encounter, LabResult, Patient, Prescription


# --------------------------------------------------------------------------- #
# API-key guard (mirrors the other edge services' FHIR adapters, e.g. norvic-hospital/clinical/fhir_views.py)
# --------------------------------------------------------------------------- #
def _check_api_key(request):
    key = request.headers.get("X-API-Key")
    return bool(key) and key == getattr(settings, "NUHRS_API_KEY", "")


def _unauthorized():
    return Response({"detail": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)


def _nid(request):
    """Platform sends the NID as ?patient=; accept ?identifier= as an alias."""
    return request.query_params.get("patient") or request.query_params.get("identifier")


def _bundle(resources):
    """Wrap a flat list of FHIR resources in a collection Bundle."""
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "total": len(resources),
        "entry": [{"resource": r} for r in resources],
    }


def _patients_for(nid):
    return Patient.objects.filter(national_id=nid)


# --------------------------------------------------------------------------- #
# Resource searches (NID-keyed, optional _id narrowing)
# --------------------------------------------------------------------------- #
@api_view(["GET"])
@permission_classes([AllowAny])
def patient_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    resources = [patient_to_fhir(p) for p in _patients_for(_nid(request))]
    return Response(_bundle(resources))


@api_view(["GET"])
@permission_classes([AllowAny])
def encounter_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    qs = Encounter.objects.filter(patient__national_id=_nid(request))
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(_bundle([encounter_to_fhir(e) for e in qs]))


@api_view(["GET"])
@permission_classes([AllowAny])
def condition_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    qs = Diagnosis.objects.filter(patient__national_id=_nid(request))
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(_bundle([condition_to_fhir(d) for d in qs]))


@api_view(["GET"])
@permission_classes([AllowAny])
def observation_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    qs = LabResult.objects.filter(patient__national_id=_nid(request))
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(_bundle([observation_to_fhir(o) for o in qs]))


@api_view(["GET"])
@permission_classes([AllowAny])
def medicationrequest_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    qs = Prescription.objects.filter(patient__national_id=_nid(request))
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(_bundle([medicationrequest_to_fhir(p) for p in qs]))


@api_view(["GET"])
@permission_classes([AllowAny])
def patient_everything(request):
    """$everything — Patient + all related clinical resources as one Bundle."""
    if not _check_api_key(request):
        return _unauthorized()
    nid = _nid(request)
    resources = []
    for p in _patients_for(nid):
        resources.append(patient_to_fhir(p))
    for e in Encounter.objects.filter(patient__national_id=nid):
        resources.append(encounter_to_fhir(e))
    for d in Diagnosis.objects.filter(patient__national_id=nid):
        resources.append(condition_to_fhir(d))
    for o in LabResult.objects.filter(patient__national_id=nid):
        resources.append(observation_to_fhir(o))
    for rx in Prescription.objects.filter(patient__national_id=nid):
        resources.append(medicationrequest_to_fhir(rx))
    return Response(_bundle(resources))
