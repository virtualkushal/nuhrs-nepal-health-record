# NUHRS — National Unified Health Record System

A prototype **Federated Health Information Exchange (HIE)** for Nepal, built with **HL7 FHIR R4**.

Hospitals and diagnostic laboratories keep ownership of their own patient data. A central
**National Platform** stores only lightweight metadata (patient identity, record index, audit
logs) and securely fetches full medical records from the originating organization on demand
using standardized FHIR APIs.

> Minor Project · Federated architecture · HL7 FHIR R4 · Nepal National ID (10-digit NIN) as patient identifier

---

## Architecture

```
                 National Platform (metadata + routing, NO clinical data)
                /       |        |         \              \
        Nepal Mediciti  Norvic   SwasthyaEHR  Central Diag Lab   Pathlabs Nepal
        (own DB+FHIR)  (own DB+FHIR) (own DB+FHIR) (own DB+FHIR)  (own DB+FHIR MySQL)
```

- **National Platform** — Master Patient Index (MPI), Provider Registry, Record Index,
  Auth (JWT + org API keys), Audit Log, and the Exchange/Routing Engine.
- **Hospital / Lab edge services** — each owns its database + exposes an HL7 FHIR read adapter.
  Two hospitals use PostgreSQL; one lab uses MySQL to prove database-engine agnosticism.
- **National Frontend** — React SPA web portal for Super Admin, Org Admin, Doctor, and Patient.
- **SwasthyaEHR** — third hospital with its own dedicated React SPA + NUHRS federation integration.


## Tech Stack

| Layer | Technology |
|---|---|
| National Frontend | React (Vite) SPA, served via nginx |
| Backend | Django + Django REST Framework |
| FHIR adapter | Custom HL7 FHIR R4 mapping layer (per edge service) |
| Database | PostgreSQL (platform + hospitals + Central lab) · MySQL (Pathlabs) |
| Interoperability | HL7 FHIR R4 |
| Auth | JWT (users) + API keys (service-to-service) |
| Orchestration | Docker Compose |


## Services & Ports

| Service | Org code | App port | DB port | Database |
|---|---|---|---|---|
| National Platform | — | 8000 | 5437 | national_db |
| Nepal Mediciti Hospital | HOSP001 | 8003 | 5438 | mediciti_db |
| Norvic International Hospital | HOSP002 | 8004 | 5439 | norvic_db |
| SwasthyaEHR Hospital | HOSP003 | 8090 | 5436 | swastha_db |
| Central Diagnostic Laboratory | LAB001 | 9001 | 5435 | lab_a_db |
| Pathlabs Nepal | LAB002 | 9002 | 3306 | lab_b_db (MySQL) |
| National Frontend | — | 3000 | — | — |
| SwasthyaEHR Frontend | — | 3090 | — | — |

> Each edge service runs as a **fully standalone application** with its own codebase,
> database, and FHIR adapter — nothing is shared between them at runtime.


## Repository Layout

```
national-platform/       Django — MPI, registry, index, audit, routing engine (NO clinical data)
mediciti-hospital/       Django — Nepal Mediciti standalone edge service (HOSP001, schema variant A)
norvic-hospital/         Django — Norvic Intl standalone edge service (HOSP002, schema variant B)
swastha-ehr/             Django + React — SwasthyaEHR hospital (HOSP003) with its own SPA
central-diagnostic-lab/  Django — Central Diagnostic Lab edge service (LAB001, PostgreSQL, variant A)
pathlabs-nepal/          Django — Pathlabs Nepal edge service (LAB002, MySQL, variant B)
frontend-react/          React (Vite) national portal, served by nginx
docs/                    Architecture, data-model, and API/flow design docs
docker-compose.yml       Orchestration for all services
seed-all.sh              Populates every facility with shared demo patients
pgadmin-servers.json     Pre-configured pgAdmin connections for every database
```

## Getting Started

**1. Start the whole federation** (6 backend services + 6 databases + 2 frontends):

```bash
docker compose up --build
```

The National Platform auto-runs its `bootstrap` command on start, creating the
Super Admin, pre-approving the five demo organizations, and creating ready-to-use
org-admin, doctor, and patient logins.

**2. Seed clinical demo data** (once the stack is healthy, in a second terminal):

```bash
./seed-all.sh
```

This populates each hospital/lab with records for the shared demo patients and
pushes their metadata to the National Platform index. (SwasthyaEHR seeds itself via
its own `seed_admin` + `seed_demo` commands — see below.)

```bash
docker compose exec swastha-backend python manage.py seed_admin
docker compose exec swastha-backend python manage.py seed_demo
```

**3. Open the portals:**
- National portal → http://localhost:3000
- SwasthyaEHR hospital app → http://localhost:3090

### Demo Credentials

| Role | Login | Password |
|---|---|---|
| Super Admin (Ministry) | `superadmin` | `admin123` |
| Org Admin | `HOSP001-ADM-0001` (also HOSP002/HOSP003/LAB001/LAB002) | `org123` |
| Doctor (ready to use) | `HOSP001-DOC-0001` (per org) | `doctor123` |
| Patient (pre-activated) | `2345678901` | `patient123` |
| Patient (self-activate) | activate with NID `2345678901` + DOB `1970-05-12` | (you choose) |

**Shared demo patients** (10-digit NIN, present across all facilities):

| NID | Name | DOB |
|---|---|---|
| `2345678901` | Ram Bahadur Thapa | 1970-05-12 |
| `2345678902` | Sita Kumari Sharma | 1988-11-23 |
| `2345678903` | Hari Prasad Koirala | 1979-02-03 |

### Try the exchange

1. Sign in as a **Doctor** (`HOSP001-DOC-0001` / `doctor123`), or create one as an Org Admin.
2. Search **`2345678901`** (Ram Bahadur Thapa).
3. Click **Fetch full unified record** — the routing engine pulls diagnoses, vitals,
   medications, allergies, and lab reports from **all facilities** into one FHIR bundle,
   each entry tagged with its source facility — even though the hospitals store their
   data in *different local schemas* (variant A vs B) and the labs run on *different
   database engines* (PostgreSQL vs MySQL). Every cross-org access is written to the audit log.


## Core Concepts

- **Federation:** the National Platform never stores clinical records — only pointers (the
  Record Index). Full detail always stays in the originating hospital/lab.
- **NID:** the Nepal National Identity Number (10-digit NIN) links a patient across all organizations.
- **FHIR adapter:** each org maps its own local schema to identical HL7 FHIR R4 output,
  regardless of column names (variant A vs B) or storage engine (PostgreSQL vs MySQL).
- **Rich clinical data:** beyond diagnoses, the federation exchanges Encounters, Vitals
  (as Observations), Medications, Allergies, Lab reports, plus Norvic-only Immunizations
  and Procedures — including Nepal-endemic conditions (Dengue, Typhoid, Tuberculosis,
  Scrub typhus, Hepatitis B) and their matching lab panels (Widal, Febrile Illness, Viral Markers).
- **Audit:** every cross-organization access is logged (actor, patient NID, action, orgs contacted).

---

*Prototype for academic purposes. Not for production clinical use.*
