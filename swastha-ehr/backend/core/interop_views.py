"""
Cross-hospital interoperability views (two-system FHIR data sharing).

Self-contained so the feature is easy to review. Provides:

- hospitals_registry          GET  /v1/hospitals/          (who am I + peers)
- OutboundShareCreateView     POST /v1/share/outbound/     (DOCTOR asks a peer)
- OutboundShareListView       GET  /v1/share/outbound/     (my outbound requests)
- OutboundSharePollView       POST /v1/share/outbound/<id>/poll/   (fetch peer status/bundle)
- OutboundShareImportView     POST /v1/share/outbound/<id>/import/  (save into our DB)
- AdminShareRequestsView      GET  /v1/admin/share-requests/        (inbound, pending)
- AdminShareDecisionView      POST /v1/admin/share-requests/<id>/decision/  (approve/deny)

Inbound requests reuse core.AccessRequest (now scope-aware). Either the patient
(portal) OR an admin (here) can approve.
"""

from datetime import timedelta

import requests
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from . import hospital_config
from .constants import AccessRequestStatus, Role
from .models import (
    AccessRequest,
    Diagnosis,
    Encounter,
    ExternalRecord,
    LabResult,
    OutboundShareRequest,
    Patient,
    Prescription,
)
from .permissions import EnforceStrictRole
from .fhir_serializers import build_everything_bundle

VALID_SCOPES = {"diagnoses", "labs", "medications", "everything"}


def scoped_bundle(patient, base_url, scope):
    """
    Build a FHIR Bundle for `patient` limited to the requested scope tokens.
    Patient is always included. Empty scope or ['everything'] returns all.
    """
    scope = [s for s in (scope or []) if s in VALID_SCOPES]
    everything = (not scope) or ("everything" in scope)

    encounters = Encounter.objects.filter(patient=patient).order_by("created_at") if everything else []
    results = (
        LabResult.objects.filter(patient=patient).order_by("created_at")
        if everything or "labs" in scope
        else []
    )
    diagnoses = (
        Diagnosis.objects.filter(patient=patient).order_by("created_at")
        if everything or "diagnoses" in scope
        else []
    )
    prescriptions = (
        Prescription.objects.filter(patient=patient).order_by("created_at")
        if everything or "medications" in scope
        else []
    )
    return build_everything_bundle(
        patient, encounters, results, diagnoses, prescriptions, base_url
    )


def _summarize_bundle(bundle):
    """Small per-resource-type count for the UI."""
    counts = {}
    for e in (bundle or {}).get("entry", []):
        rt = e.get("resource", {}).get("resourceType", "?")
        counts[rt] = counts.get(rt, 0) + 1
    return counts


def _outbound_json(o):
    return {
        "id": str(o.id),
        "peer_code": o.peer_code,
        "peer_name": o.peer_name,
        "national_id": o.national_id,
        "scope": o.scope,
        "status": o.status,
        "peer_request_id": o.peer_request_id,
        "imported": o.imported,
        "error": o.error,
        "summary": _summarize_bundle(o.bundle) if o.bundle else {},
        "created_at": o.created_at.isoformat(),
    }


# --------------------------------------------------------------------------- #
# Hospital registry
# --------------------------------------------------------------------------- #


@api_view(["GET"])
@permission_classes([EnforceStrictRole])
def hospitals_registry(request):
    """Return this hospital's identity + the peers it can request records from."""
    return Response({"self": hospital_config.identity(), "peers": hospital_config.get_peers()})


hospitals_registry.allowed_roles = [
    Role.ADMIN, Role.DOCTOR, Role.NURSE, Role.RECEPTIONIST, Role.PHARMACIST, Role.LAB_TECH,
]


# --------------------------------------------------------------------------- #
# Outbound: THIS hospital asks a PEER for a patient's records
# --------------------------------------------------------------------------- #


class OutboundShareCreateView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR]

    def post(self, request):
        peer_code = (request.data.get("peer_code") or "").strip().upper()
        national_id = (request.data.get("national_id") or "").strip()
        scope = request.data.get("scope") or []
        if not peer_code or not national_id:
            return Response({"detail": "peer_code and national_id are required."}, status=400)
        peer = hospital_config.get_peer(peer_code)
        if not peer:
            return Response({"detail": f"Unknown hospital '{peer_code}'."}, status=400)

        me = hospital_config.identity()
        o = OutboundShareRequest.objects.create(
            requested_by=request.user,
            peer_code=peer_code,
            peer_name=peer.get("name", peer_code),
            peer_base_url=peer["base_url"].rstrip("/"),
            national_id=national_id,
            scope=scope,
            status="PENDING",
        )
        # Fire the server-to-server request to the peer's public share endpoint.
        try:
            resp = requests.post(
                f"{o.peer_base_url}/api/v1/share/request/",
                json={
                    "national_id": national_id,
                    "scope": scope,
                    "requester_hospital": me["code"],
                    "requester_label": me["name"],
                },
                timeout=8,
            )
            data = resp.json()
            o.peer_request_id = str(data.get("request_id", ""))
            if not o.peer_request_id:
                o.status = "ERROR"
                o.error = data.get("detail", "Peer did not return a request id.")
        except Exception as exc:  # noqa: BLE001
            o.status = "ERROR"
            o.error = f"Could not reach {peer_code}: {exc}"
        o.save()
        return Response(_outbound_json(o), status=201)


class OutboundShareListView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR]

    def get(self, request):
        qs = OutboundShareRequest.objects.filter(requested_by=request.user)
        return Response({"results": [_outbound_json(o) for o in qs]})


class OutboundSharePollView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR]

    def post(self, request, pk):
        try:
            o = OutboundShareRequest.objects.get(pk=pk, requested_by=request.user)
        except OutboundShareRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        if not o.peer_request_id:
            return Response({"detail": "No peer request id to poll."}, status=400)
        try:
            resp = requests.get(
                f"{o.peer_base_url}/api/v1/share/request/{o.peer_request_id}/",
                timeout=8,
            )
            if resp.status_code == 200:
                # Approved: we received the FHIR Bundle.
                o.status = "APPROVED"
                o.bundle = resp.json()
            elif resp.status_code == 202:
                o.status = "PENDING"
            else:
                body = {}
                try:
                    body = resp.json()
                except Exception:  # noqa: BLE001
                    pass
                o.status = body.get("status", "DENIED")
        except Exception as exc:  # noqa: BLE001
            o.status = "ERROR"
            o.error = f"Poll failed: {exc}"
        o.save()
        return Response(_outbound_json(o))


class OutboundShareImportView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR]

    def post(self, request, pk):
        try:
            o = OutboundShareRequest.objects.get(pk=pk, requested_by=request.user)
        except OutboundShareRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        if not o.bundle:
            return Response({"detail": "Nothing to import yet (not approved)."}, status=400)
        local_patient = Patient.objects.filter(national_id=o.national_id).first()
        rec = ExternalRecord.objects.create(
            patient=local_patient,
            national_id=o.national_id,
            source_hospital_code=o.peer_code,
            source_hospital_name=o.peer_name,
            scope=o.scope,
            bundle=o.bundle,
            imported_by=request.user,
        )
        o.imported = True
        o.save(update_fields=["imported", "updated_at"])
        return Response(
            {"id": str(rec.id), "national_id": rec.national_id, "imported": True},
            status=201,
        )


# --------------------------------------------------------------------------- #
# Inbound admin approval (patient portal already handles the patient path)
# --------------------------------------------------------------------------- #


class AdminShareRequestsView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.ADMIN]

    def get(self, request):
        qs = AccessRequest.objects.all().order_by("-created_at")[:100]
        out = []
        for r in qs:
            out.append(
                {
                    "id": str(r.id),
                    "national_id": r.national_id,
                    "requester_hospital": r.requester_hospital,
                    "requester_label": r.requester_label,
                    "scope": r.scope,
                    "status": r.status,
                    "patient_known": bool(r.patient_id),
                    "created_at": r.created_at.isoformat(),
                }
            )
        return Response({"results": out})


class ExternalRecordListView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR]

    def get(self, request):
        qs = ExternalRecord.objects.all().order_by("-created_at")[:200]
        return Response({"results": [_ext_json(r) for r in qs]})


class ExternalRecordDetailView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.DOCTOR]

    def get(self, request, pk):
        try:
            r = ExternalRecord.objects.get(pk=pk)
        except ExternalRecord.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        return Response({**_ext_json(r), "sections": _parse_bundle(r.bundle)})


def _ext_json(r):
    return {
        "id": str(r.id),
        "national_id": r.national_id,
        "source_hospital_code": r.source_hospital_code,
        "source_hospital_name": r.source_hospital_name,
        "scope": r.scope,
        "created_at": r.created_at.isoformat(),
        "summary": _summarize_bundle(r.bundle),
    }


def _parse_bundle(bundle):
    """Extract readable sections from a FHIR Bundle for the UI."""
    sections = {"patient": None, "diagnoses": [], "labs": [], "medications": []}
    for entry in (bundle or {}).get("entry", []):
        res = entry.get("resource", {})
        rt = res.get("resourceType")
        if rt == "Patient":
            name = res.get("name", [{}])[0]
            sections["patient"] = {
                "name": f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip(),
                "gender": res.get("gender"),
                "birthDate": res.get("birthDate"),
                "phone": (res.get("telecom") or [{}])[0].get("value"),
            }
        elif rt == "Condition":
            sections["diagnoses"].append({
                "code": (res.get("code", {}).get("coding") or [{}])[0].get("code"),
                "display": (res.get("code", {}).get("coding") or [{}])[0].get("display")
                    or res.get("code", {}).get("text"),
                "status": res.get("clinicalStatus", {}).get("coding", [{}])[0].get("code"),
                "date": res.get("recordedDate"),
            })
        elif rt == "Observation":
            vq = res.get("valueQuantity", {})
            sections["labs"].append({
                "code": (res.get("code", {}).get("coding") or [{}])[0].get("code"),
                "display": (res.get("code", {}).get("coding") or [{}])[0].get("display")
                    or res.get("code", {}).get("text"),
                "value": vq.get("value"),
                "unit": vq.get("unit"),
                "date": res.get("effectiveDateTime"),
            })
        elif rt == "MedicationRequest":
            sections["medications"].append({
                "medication": res.get("medicationCodeableConcept", {}).get("text"),
                "dosage": (res.get("dosageInstruction") or [{}])[0].get("text"),
                "status": res.get("status"),
                "date": res.get("authoredOn"),
            })
    return sections


class AdminShareDecisionView(APIView):
    permission_classes = [EnforceStrictRole]
    allowed_roles = [Role.ADMIN]

    def post(self, request, pk):
        try:
            r = AccessRequest.objects.get(pk=pk)
        except AccessRequest.DoesNotExist:
            return Response({"detail": "Request not found."}, status=404)
        decision = (request.data.get("decision") or "").upper()
        if decision == "APPROVE":
            if not r.patient:
                r.patient = Patient.objects.filter(national_id=r.national_id).first()
            if not r.patient:
                return Response(
                    {"detail": "No local patient with that National ID to approve."},
                    status=400,
                )
            r.status = AccessRequestStatus.APPROVED
            r.approved_at = timezone.now()
            r.approved_by = request.user
            r.expires_at = timezone.now() + timedelta(minutes=30)
        elif decision == "DENY":
            r.status = AccessRequestStatus.DENIED
        else:
            return Response({"detail": "decision must be APPROVE or DENY."}, status=400)
        r.save()
        return Response({"id": str(r.id), "status": r.status})
