"""Push record metadata to the National Platform (metadata only)."""
import requests
from django.conf import settings


def push_index(nid, patient_meta, resource_type, local_record_id, service_date, summary):
    url = f"{settings.PLATFORM_URL.rstrip('/')}/api/index/"
    payload = {
        "nid": nid,
        "patient": patient_meta,
        "resource_type": resource_type,
        "local_record_id": str(local_record_id),
        "service_date": service_date,
        "summary": summary,
    }
    try:
        resp = requests.post(
            url, json=payload,
            headers={"X-API-Key": settings.ORG_API_KEY},
            timeout=6,
        )
        return resp.status_code, resp.json()
    except requests.RequestException as exc:
        return None, {"detail": f"platform unreachable: {exc}"}
