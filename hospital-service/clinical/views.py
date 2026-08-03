"""
Local hospital data-entry API (used by hospital staff UI).

Creating a Condition/Observation/Encounter also pushes a metadata pointer to
the National Platform so the record becomes discoverable nationwide.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import fhir, services
from .models import Condition, Encounter, LocalPatient, Observation
from .validators import NIDValidationError, validate_nid



VARIANT = settings.SCHEMA_VARIANT


def _patient_meta(p):
    return {
        "nid": p.nid,
        "full_name": fhir.patient_name(p),
        "date_of_birth": p.dob.isoformat() if p.dob else None,
        "gender": (p.gender or "OTHER").upper(),
        "phone": p.phone,
    }


def _get_or_create_patient(data):
    nid = validate_nid(data.get("nid"))
    defaults = {

        "dob": data.get("dob"),
        "gender": data.get("gender", ""),
        "phone": data.get("phone", ""),
        "mrn": data.get("mrn", ""),
    }
    name = data.get("name", "")
    if VARIANT == "B":
        parts = name.split(" ", 1)
        defaults["first_name"] = parts[0]
        defaults["last_name"] = parts[1] if len(parts) > 1 else ""
    else:
        defaults["full_name"] = name
    patient, _ = LocalPatient.objects.get_or_create(nid=nid, defaults=defaults)
    return patient


@api_view(["GET"])
def whoami(request):
    return Response({
        "org_name": settings.ORG_NAME,
        "org_code": settings.ORG_CODE,
        "schema_variant": VARIANT,
        "type": "HOSPITAL",
    })


@api_view(["GET"])
def list_patients(request):
    patients = LocalPatient.objects.all().order_by("-created_at")[:100]
    return Response([_patient_meta(p) for p in patients])


@api_view(["POST"])
def create_condition(request):
    """Register a diagnosis and index it nationally."""
    data = request.data
    try:
        patient = _get_or_create_patient(data)
    except NIDValidationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    kwargs = {"patient": patient}
    text = data.get("diagnosis", "")

    code = data.get("icd10", "")
    onset = data.get("onset_date")
    if VARIANT == "B":
        kwargs.update({"condition_desc": text, "icd_code": code, "status": "active", "onset": onset})
    else:
        kwargs.update({"diagnosis_text": text, "icd10_code": code, "clinical_status": "active", "onset_date": onset})

    condition = Condition.objects.create(**kwargs)

    code_status, resp = services.push_index(
        nid=patient.nid, patient_meta=_patient_meta(patient),
        resource_type="Condition", local_record_id=condition.id,
        service_date=onset or data.get("service_date"),
        summary=text,
    )
    return Response(
        {"local_id": condition.id, "fhir": fhir.to_fhir_condition(condition), "index_status": code_status},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def create_observation(request):
    data = request.data
    try:
        patient = _get_or_create_patient(data)
    except NIDValidationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    kwargs = {"patient": patient}
    name = data.get("name", "")

    value = data.get("value", "")
    unit = data.get("unit", "")
    date = data.get("date")
    if VARIANT == "B":
        kwargs.update({"measurement_name": name, "measurement_value": value, "measurement_unit": unit, "taken_on": date})
    else:
        kwargs.update({"obs_type": name, "value": value, "unit": unit, "observed_date": date})

    obs = Observation.objects.create(**kwargs)

    code_status, _ = services.push_index(
        nid=patient.nid, patient_meta=_patient_meta(patient),
        resource_type="Observation", local_record_id=obs.id,
        service_date=date, summary=f"{name}: {value} {unit}".strip(),
    )
    return Response(
        {"local_id": obs.id, "fhir": fhir.to_fhir_observation(obs), "index_status": code_status},
        status=status.HTTP_201_CREATED,
    )
