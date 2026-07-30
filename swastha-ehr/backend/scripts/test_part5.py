"""
Ad-hoc end-to-end test for Part 5 (lab orders/results + FHIR export).

Uses only the Python standard library so it needs no extra dependency.
Run against a live local server (after `seed_demo`):

    venv\\Scripts\\python.exe scripts\\test_part5.py

Exits non-zero on the first failed assertion.
"""

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
PW = "demo12345"


def call(method, path, token=None, body=None):
    """Return (status_code, parsed_json_or_none, content_type)."""
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            ctype = resp.headers.get("Content-Type", "")
            return resp.status, (json.loads(raw) if raw else None), ctype
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        ctype = e.headers.get("Content-Type", "")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return e.code, parsed, ctype


def login(username, password):
    status, data, _ = call(
        "POST", "/api/v1/auth/login/", body={"username": username, "password": password}
    )
    assert status == 200, f"login failed for {username}: {status} {data}"
    return data["access"]


def main():
    doctor = login("doctor", PW)
    labtech = login("labtech", PW)

    # Pick a patient (Ram Bahadur) via the doctor's directory.
    _, patients, _ = call("GET", "/api/v1/patients/?search=Ram", token=doctor)
    assert patients, "No patient found — did you run seed_demo?"
    patient = patients[0]
    pid = patient["id"]
    print(f"[ok] patient: {patient['first_name']} {patient['last_name']} ({pid})")

    # 1) Doctor orders a Hemoglobin test.
    status, order, _ = call(
        "POST",
        "/api/v1/lab-orders/",
        token=doctor,
        body={"patient": pid, "test_name": "HEMOGLOBIN", "priority": "URGENT"},
    )
    assert status == 201, f"order create failed: {status} {order}"
    assert order["loinc_code"] == "718-7", "LOINC not derived correctly"
    print(f"[ok] doctor ordered lab test, loinc={order['loinc_code']}")

    # 2) Lab tech sees it in the queue.
    _, queue, _ = call("GET", "/api/v1/lab-orders/", token=labtech)
    assert any(o["id"] == order["id"] for o in queue), "order not in lab queue"
    print(f"[ok] order visible in lab queue ({len(queue)} pending)")

    # 3) Out-of-range result is rejected (Hemoglobin max is 25).
    status, body, _ = call(
        "POST",
        "/api/v1/lab-observations/",
        token=labtech,
        body={
            "patient": pid,
            "lab_order": order["id"],
            "test_name": "HEMOGLOBIN",
            "result_value": 99.0,
        },
    )
    assert status == 400, f"expected 400 for out-of-range, got {status}"
    print(f"[ok] out-of-range value rejected: {body}")

    # 4) Valid result is accepted; order auto-closes.
    status, obs, _ = call(
        "POST",
        "/api/v1/lab-observations/",
        token=labtech,
        body={
            "patient": pid,
            "lab_order": order["id"],
            "test_name": "HEMOGLOBIN",
            "result_value": 14.20,
        },
    )
    assert status == 201, f"result create failed: {status} {obs}"
    assert obs["result_unit"] == "g/dL", "unit not derived"
    print(f"[ok] result saved obs={obs['id']} unit={obs['result_unit']}")

    _, queue2, _ = call("GET", "/api/v1/lab-orders/", token=labtech)
    assert not any(o["id"] == order["id"] for o in queue2), "order did not close"
    print("[ok] order auto-closed after result")

    # 5) FHIR Observation export.
    status, fobs, ctype = call(
        "GET", f"/api/fhir/v1/Observation/{obs['id']}/", token=doctor
    )
    assert status == 200, f"fhir observation failed: {status}"
    assert "application/fhir+json" in ctype, f"wrong mimetype: {ctype}"
    assert fobs["resourceType"] == "Observation"
    assert fobs["code"]["coding"][0]["code"] == "718-7"
    assert fobs["valueQuantity"]["value"] == 14.2
    assert fobs["valueQuantity"]["system"] == "http://unitsofmeasure.org"
    print("[ok] FHIR Observation valid + correct mimetype")

    # 6) FHIR Patient export.
    status, fpat, _ = call("GET", f"/api/fhir/v1/Patient/{pid}/", token=doctor)
    assert status == 200
    assert fpat["resourceType"] == "Patient"
    assert fpat["gender"] in ("male", "female", "other", "unknown")
    print("[ok] FHIR Patient valid")

    # 7) FHIR $everything Bundle.
    status, bundle, _ = call(
        "GET", f"/api/fhir/v1/Patient/{pid}/$everything/", token=doctor
    )
    assert status == 200, f"bundle failed: {status} {bundle}"
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert bundle["total"] >= 2
    print(f"[ok] FHIR Bundle valid, total={bundle['total']}")

    # 8) A pharmacist may read FHIR but a receptionist may not.
    pharmacist = login("pharmacist", PW)
    status, _, _ = call("GET", f"/api/fhir/v1/Patient/{pid}/", token=pharmacist)
    assert status == 200, "pharmacist should read FHIR"
    reception = login("reception", PW)
    status, _, _ = call("GET", f"/api/fhir/v1/Patient/{pid}/", token=reception)
    assert status == 403, f"receptionist should be blocked, got {status}"
    print("[ok] FHIR RBAC: pharmacist allowed, receptionist blocked")

    print("\nALL PART 5 CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\nCONNECTION ERROR: {e} — is the server running on :8000?")
        sys.exit(1)
