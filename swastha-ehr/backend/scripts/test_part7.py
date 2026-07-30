"""
Ad-hoc end-to-end test for Part 7 (patient self-registration login + portal).

Standard library only. Run against a live local server after `seed_demo`:

    venv\\Scripts\\python.exe scripts\\test_part7.py

Covers:
  1. Public self-registration WITH credentials creates a working login.
  2. That patient can sign in and read ONLY their own data at /portal/me/.
  3. A patient is blocked (403) from staff/FHIR endpoints (RBAC holds).
  4. Public self-registration WITHOUT credentials still works (has_login=false).
  5. Duplicate usernames are rejected.

Exits non-zero on the first failed assertion.
"""

import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
PW = "demo12345"


def call(method, path, token=None, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return e.code, parsed


def login(username, password):
    status, data = call(
        "POST", "/api/v1/auth/login/", body={"username": username, "password": password}
    )
    assert status == 200, f"login failed for {username}: {status} {data}"
    return data["access"]


def main():
    # Unique username each run so the script is re-runnable.
    uname = f"portaltest{int(time.time())}"

    # 1) Self-register WITH a portal login.
    status, created = call(
        "POST",
        "/api/v1/patients/register/",
        body={
            "first_name": "Portal",
            "last_name": "Tester",
            "phone_number": "+977-9800000000",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "allergies": ["Penicillin"],
            "username": uname,
            "password": PW,
        },
    )
    assert status == 201, f"register w/ login failed: {status} {created}"
    assert created.get("has_login") is True, "expected has_login=true"
    pid = created["id"]
    print(f"[ok] self-registered with login: {uname} ({created['hospital_identifier']})")

    # 2) Patient can sign in and read their own portal data.
    patient_token = login(uname, PW)
    status, me = call("GET", "/api/v1/portal/me/", token=patient_token)
    assert status == 200, f"portal/me failed: {status} {me}"
    for key in ("patient", "observations", "prescriptions", "trends"):
        assert key in me, f"portal payload missing '{key}'"
    assert me["patient"]["id"] == pid, "portal returned the wrong patient!"
    assert me["patient"]["allergies"] == ["Penicillin"]
    print("[ok] patient can read own scoped portal data")

    # 3) RBAC: patient is blocked from staff + FHIR endpoints.
    status, _ = call("GET", "/api/v1/patients/", token=patient_token)
    assert status == 403, f"patient should NOT list patients, got {status}"
    status, _ = call("GET", f"/api/fhir/v1/Patient/{pid}/", token=patient_token)
    assert status == 403, f"patient should NOT read FHIR, got {status}"
    print("[ok] RBAC: patient blocked from staff/FHIR endpoints (403)")

    # 4) Self-register WITHOUT credentials still works.
    status, plain = call(
        "POST",
        "/api/v1/patients/register/",
        body={
            "first_name": "NoLogin",
            "last_name": "Walkin",
            "phone_number": "+977-9811111111",
            "date_of_birth": "1985-06-15",
            "gender": "female",
            "allergies": ["None"],
        },
    )
    assert status == 201, f"register w/o login failed: {status} {plain}"
    assert plain.get("has_login") is False, "expected has_login=false"
    print("[ok] self-registration without credentials still works")

    # 5) Duplicate username is rejected.
    status, dup = call(
        "POST",
        "/api/v1/patients/register/",
        body={
            "first_name": "Dupe",
            "last_name": "User",
            "phone_number": "+977-9822222222",
            "date_of_birth": "1992-02-02",
            "gender": "male",
            "allergies": ["None"],
            "username": uname,  # already taken above
            "password": PW,
        },
    )
    assert status == 400, f"duplicate username should be 400, got {status} {dup}"
    print("[ok] duplicate username rejected (400)")

    print("\nALL PART 7 CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\nCONNECTION ERROR: {e} — is the server running on :8000?")
        sys.exit(1)
