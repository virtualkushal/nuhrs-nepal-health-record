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
- **National Frontend** — React portal for Super Admin, Org Admin, Doctor, and Patient.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Django + Django REST Framework |
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
| National Frontend | 5173 | — |

## Repository Layout

```
national-platform/   Django — MPI, registry, index, audit, routing engine
hospital-service/    Django — reusable hospital data source + FHIR adapter
lab-service/         Django — reusable lab data source + FHIR adapter
frontend/            React — national portal
docker-compose.yml   Orchestration for all services
```

## Getting Started

```bash
docker compose up --build
```

Then open the frontend at http://localhost:5173

## Core Concepts

- **Federation:** the National Platform never stores clinical records — only pointers.
- **NID:** the Nepal National Identity Number links a patient across all organizations.
- **FHIR adapter:** each org maps its own local schema to identical FHIR output.
- **Audit:** every cross-organization access is logged.

---

*Prototype for academic purposes. Not for production clinical use.*
