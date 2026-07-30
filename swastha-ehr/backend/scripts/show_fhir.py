"""Print live FHIR R4 JSON for a demo patient + one of their observations."""
import json, urllib.request, urllib.error

BASE = "http://127.0.0.1:8000"


def call(method, path, token=None, body=None, fhir=False):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return resp.status, resp.headers.get("Content-Type"), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type"), e.read().decode()


_, _, login = call("POST", "/api/v1/auth/login/", body={"username": "doctor", "password": "demo12345"})
token = login["access"]

# Find a patient that has observations (Sita).
_, _, patients = call("GET", "/api/v1/patients/", token=token)
target = next((p for p in patients if p["first_name"] == "Sita"), patients[0])
pid = target["id"]

print("=" * 70)
print(f"GET /api/fhir/v1/Patient/{pid}/")
st, ct, body = call("GET", f"/api/fhir/v1/Patient/{pid}/", token=token)
print(f"[{st}] Content-Type: {ct}")
print(json.dumps(body, indent=2))

print("=" * 70)
print(f"GET /api/fhir/v1/Patient/{pid}/$everything/")
st, ct, body = call("GET", f"/api/fhir/v1/Patient/{pid}/$everything/", token=token)
print(f"[{st}] Content-Type: {ct}")
print(json.dumps(body, indent=2)[:2000])
