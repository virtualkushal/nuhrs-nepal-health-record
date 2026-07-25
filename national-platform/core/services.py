"""
Service layer for the National Platform.

Contains:
- credential generation for organization approval
- the Exchange / Routing Engine (the heart of the federation)
"""
import secrets
import string

import requests

from .models import AuditLog, Organization, RecordIndex


# ---------------------------------------------------------------------------
# Organization approval credential generation
# ---------------------------------------------------------------------------
def generate_org_code(org_type: str) -> str:
    prefix = "HOSP" if org_type == Organization.OrgType.HOSPITAL else "LAB"
    count = Organization.objects.filter(
        organization_type=org_type, organization_code__isnull=False
    ).count()
    return f"{prefix}{count + 1:03d}"


def generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits + "@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key() -> str:
    return secrets.token_hex(32)


def generate_admin_username(org_code: str) -> str:
    return f"{org_code}-ADM-0001"


# ---------------------------------------------------------------------------
# Exchange / Routing Engine
# ---------------------------------------------------------------------------
class RoutingEngine:
    """
    Given a patient NID, resolve which organizations hold their records and
    fetch the actual clinical data from those orgs via their FHIR adapters.

    The platform never stores this data — it is fetched on demand and returned
    transiently to the caller.
    """

    FETCH_TIMEOUT = 8  # seconds

    def __init__(self, actor_user=None, ip_address=None):
        self.actor_user = actor_user
        self.ip_address = ip_address

    # -- public operations --------------------------------------------------
    def fetch_all(self, nid: str) -> dict:
        """Fetch every indexed record for a patient across all owning orgs."""
        indices = RecordIndex.objects.filter(patient__nid=nid).select_related("organization")
        org_ids = {idx.organization_id for idx in indices}
        organizations = Organization.objects.filter(id__in=org_ids)

        entries = []
        contacted = []
        for org in organizations:
            contacted.append(org.organization_name)
            bundle = self._request_everything(org, nid)
            entries.extend(bundle)

        self._audit(nid, AuditLog.Action.FETCH_ALL, contacted)
        return self._wrap_bundle(entries)

    def fetch_one(self, nid: str, record_index_id: int) -> dict:
        """Fetch a single specific record."""
        idx = RecordIndex.objects.select_related("organization").get(
            id=record_index_id, patient__nid=nid
        )
        org = idx.organization
        resource = self._request_resource(org, idx.resource_type, nid, idx.local_record_id)
        self._audit(nid, AuditLog.Action.FETCH_ONE, [org.organization_name], record_index=idx)
        entries = [resource] if resource else []
        return self._wrap_bundle(entries)

    # -- outbound FHIR calls ------------------------------------------------
    def _headers(self, org: Organization) -> dict:
        # Signal FHIR JSON but also accept plain application/json, since the
        # org FHIR adapters serve via DRF's default JSON renderer. Without the
        # fallback, content negotiation returns 406 Not Acceptable.
        return {
            "X-API-Key": org.api_key or "",
            "Accept": "application/fhir+json, application/json",
        }

    def _request_everything(self, org: Organization, nid: str) -> list:
        url = f"{org.api_base_url.rstrip('/')}/$everything"
        try:
            resp = requests.get(
                url, params={"patient": nid}, headers=self._headers(org),
                timeout=self.FETCH_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            return [e["resource"] for e in data.get("entry", []) if "resource" in e]
        except requests.RequestException as exc:
            return [self._unavailable(org, str(exc))]

    def _request_resource(self, org: Organization, resource_type: str, nid: str, local_id: str):
        url = f"{org.api_base_url.rstrip('/')}/{resource_type}"
        try:
            resp = requests.get(
                url, params={"patient": nid, "_id": local_id},
                headers=self._headers(org), timeout=self.FETCH_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("resourceType") == "Bundle":
                entries = [e["resource"] for e in data.get("entry", []) if "resource" in e]
                return entries[0] if entries else None
            return data
        except requests.RequestException as exc:
            return self._unavailable(org, str(exc))

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _unavailable(org: Organization, detail: str) -> dict:
        return {
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "warning",
                "code": "transient",
                "diagnostics": f"Source '{org.organization_name}' unavailable: {detail}",
            }],
            "_source": org.organization_name,
        }

    @staticmethod
    def _wrap_bundle(entries: list) -> dict:
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "total": len(entries),
            "entry": [{"resource": r} for r in entries],
        }

    def _audit(self, nid, action, contacted, record_index=None):
        actor_org = getattr(self.actor_user, "organization", None)
        AuditLog.objects.create(
            actor_user=self.actor_user,
            actor_org=actor_org,
            nid=nid,
            record_index=record_index,
            action=action,
            target_orgs=", ".join(contacted),
            ip_address=self.ip_address,
        )
