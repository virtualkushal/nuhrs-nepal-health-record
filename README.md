# NUHRS — National Unified Health Record System

A prototype **Federated Health Information Exchange (HIE)** for Nepal, built with **HL7 FHIR R4**.

Hospitals and diagnostic laboratories keep ownership of their own patient data. A central
**National Platform** stores only lightweight metadata (patient identity, record index, audit
logs) and securely fetches full medical records from the originating organization on demand
using standardized FHIR APIs.

> Minor Project · Federated architecture · HL7 FHIR R4 · Nepal National ID (NID) as patient identifier

---

## Architecture

```
                 National Platform (metadata + routing, NO clinical data)
                 /            |              \              \
        Nepal Mediciti    Norvic Intl    Central Diag Lab   Pathlabs Nepal
        (own DB + FHIR)  (own DB + FHIR) (own DB + FHIR)    (own DB + FHIR)
```

- **National Platform** — Master Patient Index (MPI), Provider Registry, Record Index,
  Auth (JWT + org API keys), Audit Log, and the Exchange/Routing Engine.
- **Hospital / Lab services** — own PostgreSQL database + an HL7 FHIR read adapter.
- **National Frontend** — web portal for Super Admin, Org Admin, Doctor, and Patient.


## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla JS SPA (served via nginx) |
| Backend | Django + Django REST Framework |
| FHIR adapter | Custom HL7 FHIR R4 mapping layer |
| Database | PostgreSQL |
| Interoperability | HL7 FHIR R4 |
| Auth | JWT (users) + API keys (service-to-service) |
| Orchestration | Docker Compose |


## Services & Ports

| Service | Port | Database |
|---|---|---|
| National Platform | 8000 | national_db |
| Nepal Mediciti Hospital | 8001 | hospital_a_db |
| Norvic International Hospital | 8002 | hospital_b_db |
| Central Diagnostic Laboratory | 9001 | lab_a_db |
| Pathlabs Nepal | 9002 | lab_b_db |
| National Frontend | 3000 | — |


## Repository Layout

```
national-platform/   Django — MPI, registry, index, audit, routing engine
hospital-service/    Django — reusable hospital data source + FHIR adapter
lab-service/         Django — reusable lab data source + FHIR adapter
frontend/            Vanilla-JS national portal (served by nginx)
docker-compose.yml   Orchestration for all services
seed-all.sh          Populates every facility with shared demo patients
```

## Getting Started

**1. Start the whole federation** (5 services + 5 databases + frontend):

```bash
docker compose up --build
```

The National Platform auto-runs its `bootstrap` command on start, creating the
Super Admin and pre-approving the four demo organizations.

**2. Seed clinical demo data** (once the stack is healthy, in a second terminal):

```bash
./seed-all.sh
```

This populates each hospital/lab with records for the shared demo patients and
pushes their metadata to the National Platform index.

**3. Open the portal:** http://localhost:3000

### Demo Credentials

| Role | Login | Password |
|---|---|---|
| Super Admin (Ministry) | `superadmin` | `admin123` |
| Org Admin (e.g. Mediciti) | `HOSP001-ADM-0001` | `org123` |
| Patient | activate with `NID-1001` + DOB `1975-04-12` | (you choose) |

### Try the exchange

1. Sign in as an **Org Admin** and create a **Doctor** login.
2. Sign in as that doctor, search **`NID-1001`** (Ram Bahadur Thapa).
3. Click **Fetch full unified record** — the routing engine pulls diagnoses from
   both hospitals and lab reports from both labs into one FHIR bundle, each
   tagged with its source facility — even though the two hospitals store their
   data in *different local schemas* (variant A vs B).


## Core Concepts

- **Federation:** the National Platform never stores clinical records — only pointers.
- **NID:** the Nepal National Identity Number links a patient across all organizations.
- **FHIR adapter:** each org maps its own local schema to identical FHIR output.
- **Audit:** every cross-organization access is logged.

---

*Prototype for academic purposes. Not for production clinical use.*
