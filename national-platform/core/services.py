"""
Service layer for the National Platform.

Contains:
- credential generation for organization approval
- the Exchange / Routing Engine (the heart of the federation)
"""
import secrets
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from django.conf import settings

from .models import AuditLog, Organization, RecordIndex, User


# ---------------------------------------------------------------------------
# Login resolution
# ---------------------------------------------------------------------------
def resolve_login_user(*, scope, org_code=None, login_name=None, username=None):
    """
    Resolve the internal User for a login attempt, given the login *scope*.

    The frontend login card offers these scopes (a toggle):
      - "STAFF"    -> org_code + login_name  (role auto-detected from the user)
      - "PATIENT"  -> username is the 11-digit NID
      - "OFFICIAL" -> username of a privileged account; resolves EITHER a Super
                      Admin OR a Ministry user. The caller routes to the right
                      dashboard based on the returned account's actual role.

    "MINISTRY" is accepted as a backward-compatible alias for "OFFICIAL".

    Returns the matching User instance, or None if no unique match is found.
    Password verification is done by the caller.
    """
    scope = (scope or "STAFF").upper()

    if scope in ("OFFICIAL", "MINISTRY"):
        return (
            User.objects.filter(
                username=(username or "").strip(),
                role__in=[User.Role.SUPER_ADMIN, User.Role.MINISTRY],
            ).first()
        )

    if scope == "PATIENT":
        return (
            User.objects.filter(username=(username or "").strip(),
                                 role=User.Role.PATIENT).first()
        )

    # STAFF: resolve within an organization by the human-friendly login_name.
    org_code = (org_code or "").strip()
    login_name = (login_name or "").strip()
    if not org_code or not login_name:
        return None
    try:
        org = Organization.objects.get(organization_code__iexact=org_code)
    except Organization.DoesNotExist:
        return None
    # Suspended / pending / rejected orgs cannot authenticate staff. This makes
    # the Ministry's suspend action immediately effective at the login gate.
    if org.status != Organization.Status.ACTIVE:
        return None
    # Match on login_name first (new scheme); fall back to full username so
    # legacy-style entries (e.g. HOSP001-DOC-0001) still work during transition.
    return (
        User.objects.filter(organization=org, login_name__iexact=login_name).first()
        or User.objects.filter(organization=org, username__iexact=login_name).first()
    )


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

    FETCH_TIMEOUT = getattr(settings, "NUHRS_FETCH_TIMEOUT", 8)  # seconds

    def __init__(self, actor_user=None, ip_address=None):
        self.actor_user = actor_user
        self.ip_address = ip_address

    # -- public operations --------------------------------------------------
    def fetch_all(self, nid: str) -> dict:
        """Fetch every indexed record for a patient across all owning orgs.

        Requests to each owning organization run concurrently on a worker
        pool. Results are merged back in the original organization order so
        the response stays deterministic regardless of completion order.
        """
        indices = RecordIndex.objects.filter(patient__nid=nid).select_related("organization")
        org_ids = {idx.organization_id for idx in indices}
        organizations = list(Organization.objects.filter(id__in=org_ids).order_by("id"))

        max_workers = getattr(settings, "NUHRS_FETCH_WORKERS", 4)
        per_org_results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._request_everything, org, nid): org
                for org in organizations
            }
            for future in as_completed(futures):
                org = futures[future]
                try:
                    per_org_results[org.id] = future.result()
                except Exception as exc:
                    per_org_results[org.id] = [self._unavailable(org, str(exc))]

        entries = []
        for org in organizations:
            entries.extend(
                per_org_results.get(
                    org.id, [self._unavailable(org, "no result for organization")]
                )
            )

        self._audit(
            nid,
            AuditLog.Action.FETCH_ALL,
            [org.organization_name for org in organizations],
        )
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
