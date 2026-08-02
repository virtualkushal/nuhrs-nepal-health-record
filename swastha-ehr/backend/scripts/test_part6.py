"""
Ad-hoc end-to-end test for Part 6 (doctor clinical timeline + lab trends).

Standard library only. Run against a live local server after `seed_demo`
(and ideally after running test_part5.py once so there is at least one lab
result to plot):

    venv\\Scripts\\python.exe scripts\\test_part6.py

Exits non-zero on the first failed assertion.
"""

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
PW = "demo12345"


def call(method, path, token=None, body=None):
    """Return (status_code, parsed_json_or_none)."""
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
    doctor = login("doctor", PW)

    # Pick a patient (Ram Bahadur) via the doctor's directory.
    _, patients = call("GET", "/api/v1/patients/?search=Ram", token=doctor)
    assert patients, "No patient found — did you run seed_demo?"
    patient = patients[0]
    pid = patient["id"]
    print(f"[ok] patient: {patient['first_name']} {patient['last_name']} ({pid})")

    # 1) Doctor can fetch the clinical timeline.
    status, timeline = call("GET", f"/api/v1/patients/{pid}/timeline/", token=doctor)
    assert status == 200, f"timeline failed: {status} {timeline}"
    for key in ("patient", "prescriptions", "observations", "trends"):
        assert key in timeline, f"timeline missing '{key}'"
    print(
        f"[ok] timeline: {len(timeline['prescriptions'])} rx, "
        f"{len(timeline['observations'])} obs, {len(timeline['trends'])} trend series"
    )

    # 2) Each trend series is shaped correctly for the chart component.
    for series in timeline["trends"]:
        assert "test_name" in series and "unit" in series and "points" in series
        for pt in series["points"]:
            assert "date" in pt and "value" in pt
            assert isinstance(pt["value"], (int, float)), "value must be numeric"
    print("[ok] trend series shape valid (date + numeric value)")

    # 3) Points within a series are in chronological (ascending) order.
    for series in timeline["trends"]:
        dates = [p["date"] for p in series["points"]]
        assert dates == sorted(dates), f"{series['test_name']} points not time-ordered"
    print("[ok] trend points are time-ordered")

    # 4) RBAC: the timeline is DOCTOR-only.
    reception = login("reception", PW)
    status, _ = call("GET", f"/api/v1/patients/{pid}/timeline/", token=reception)
    assert status == 403, f"receptionist should be blocked, got {status}"

    labtech = login("labtech", PW)
    status, _ = call("GET", f"/api/v1/patients/{pid}/timeline/", token=labtech)
    assert status == 403, f"lab tech should be blocked, got {status}"

    status, _ = call("GET", f"/api/v1/patients/{pid}/timeline/")
    assert status == 401, f"anonymous should be 401, got {status}"
    print("[ok] RBAC: doctor allowed; receptionist/labtech 403; anon 401")

    print("\nALL PART 6 CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\nCONNECTION ERROR: {e} — is the server running on :8000?")
        sys.exit(1)
