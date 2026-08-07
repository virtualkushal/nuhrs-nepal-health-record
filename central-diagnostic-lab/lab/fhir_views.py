"""FHIR REST endpoints (read-only) exposed to the National Platform."""
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import fhir
from .models import LabPatient, LabReport


def _check_api_key(request):
    return request.headers.get("X-API-Key") == settings.ORG_API_KEY


def _unauthorized():
    return Response({"detail": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["GET"])
def patient_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("identifier") or request.query_params.get("patient")
    patients = LabPatient.objects.filter(nid=nid)
    return Response(fhir.make_bundle([fhir.to_fhir_patient(p) for p in patients]))


@api_view(["GET"])
def diagnostic_report_search(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    qs = LabReport.objects.filter(patient__nid=nid).prefetch_related("results")
    if request.query_params.get("_id"):
        qs = qs.filter(id=request.query_params["_id"])
    return Response(fhir.make_bundle([fhir.to_fhir_diagnostic_report(r) for r in qs]))


@api_view(["GET"])
def patient_everything(request):
    if not _check_api_key(request):
        return _unauthorized()
    nid = request.query_params.get("patient")
    resources = []
    for p in LabPatient.objects.filter(nid=nid):
        resources.append(fhir.to_fhir_patient(p))
    for r in LabReport.objects.filter(patient__nid=nid).prefetch_related("results"):
        resources.append(fhir.to_fhir_diagnostic_report(r))
    return Response(fhir.make_bundle(resources))
