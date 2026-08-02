"""
This hospital's identity + the registry of peer hospitals it can exchange
records with. Env-driven so the SAME codebase runs as two independent instances
(Hospital 1 and Hospital 2), each with its own database, ports, and branding.

Env vars:
  HOSPITAL_CODE   short code for THIS instance, e.g. "H1" (default "H1")
  HOSPITAL_NAME   display name, e.g. "Hospital 1"          (default "Hospital 1")
  HOSPITAL_PEERS  JSON list of peer hospitals, e.g.
                  '[{"code":"H2","name":"Hospital 2","base_url":"http://localhost:8001"}]'
                  If unset, a sensible dev default is used (H1 knows H2 and vice versa).
"""

import json
import os

DEFAULT_PEERS = {
    "H1": [{"code": "H2", "name": "Hospital 2", "base_url": "http://localhost:8001"}],
    "H2": [{"code": "H1", "name": "Hospital 1", "base_url": "http://localhost:8000"}],
}


def get_hospital_code():
    return os.getenv("HOSPITAL_CODE", "H1").strip().upper()


def get_hospital_name():
    return os.getenv("HOSPITAL_NAME", f"Hospital {get_hospital_code()[-1]}").strip()


def get_peers():
    """Return the list of peer hospitals this instance can talk to."""
    raw = os.getenv("HOSPITAL_PEERS", "").strip()
    if raw:
        try:
            peers = json.loads(raw)
            if isinstance(peers, list):
                return peers
        except json.JSONDecodeError:
            pass
    return DEFAULT_PEERS.get(get_hospital_code(), [])


def get_peer(code):
    """Look up a single peer hospital by its code (case-insensitive)."""
    code = (code or "").strip().upper()
    for p in get_peers():
        if p.get("code", "").upper() == code:
            return p
    return None


def identity():
    """This hospital's own identity, for the /v1/hospitals/ response and FHIR base."""
    return {"code": get_hospital_code(), "name": get_hospital_name()}
