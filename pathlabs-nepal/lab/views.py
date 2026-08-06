"""
Local lab data-entry API (used by lab technician UI).

Creating a LabReport also pushes a DiagnosticReport metadata pointer to the
National Platform so the report becomes discoverable nationwide.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import fhir, services
from .models import LabPatient, LabReport, LabResult
from .validators import NIDValidationError, validate_nid


def _patient_meta(p):
    return {
        "nid": p.nid,
        "full_name": f"{p.given_name} {p.surname}".strip(),
        "date_of_birth": p.dob.isoformat() if p.dob else None,
        "gender": (p.gender or "OTHER").upper(),
        "phone": p.phone,
    }


def _get_or_create_patient(data):
    name = data.get("name", "")
    parts = name.split(" ", 1)
    defaults = {
        "dob": data.get("dob"),
        "gender": data.get("gender", ""),
        "phone": data.get("phone", ""),
        "given_name": parts[0],
        "surname": parts[1] if len(parts) > 1 else "",
    }
    nid = validate_nid(data.get("nid"))
    patient, _ = LabPatient.objects.get_or_create(nid=nid, defaults=defaults)
    return patient


@api_view(["GET"])
def whoami(request):
    return Response({
        "org_name": settings.ORG_NAME,
        "org_code": settings.ORG_CODE,
        "type": "LAB",
    })


@api_view(["GET"])
def list_patients(request):
    patients = LabPatient.objects.all().order_by("-created_at")[:100]
    return Response([_patient_meta(p) for p in patients])


@api_view(["POST"])
def create_report(request):
    """
    Create a lab report with result lines and index it nationally.
    Body: { nid, name, dob, gender, phone, panel, doctor, date, conclusion,
            results: [ {name, value, unit, range}, ... ] }
    """
    data = request.data
    try:
        patient = _get_or_create_patient(data)
    except NIDValidationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    panel = data.get("panel", "")
    doctor = data.get("doctor", "")
    date = data.get("date")
    conclusion = data.get("conclusion", "")

    report = LabReport.objects.create(
        patient=patient, test_panel=panel, referred_by=doctor,
        reported_on=date, interpretation=conclusion)

    for line in data.get("results", []):
        LabResult.objects.create(
            report=report, test_name=line.get("name", ""), value=line.get("value", ""),
            uom=line.get("unit", ""), normal_range=line.get("range", ""))

    code_status, _ = services.push_index(
        nid=patient.nid, patient_meta=_patient_meta(patient),
        resource_type="DiagnosticReport", local_record_id=report.id,
        service_date=date, summary=panel or "Lab Report",
    )
    return Response(
        {"local_id": report.id, "fhir": fhir.to_fhir_diagnostic_report(
            report), "index_status": code_status},
        status=status.HTTP_201_CREATED,
    )
