# NUHRS — Demo Data Catalog & Access Guide

Everything you can look at in the demo federation, where it lives, and exactly
how to open it. Applies to the current seeded state (5 facilities + national
platform + SwasthyaEHR).

---

## 1. Quick start — view it in the browser

### Doctor view (unified cross-facility record)

1. Open **http://localhost:3000** → tab **Doctor** (or **Staff**).
2. Login: scope **Staff**, Org Code `HOSP001`, Login `doctor`, Password `doctor123`.
3. Type any NID from the catalog below in **SEARCH PATIENT** and press Enter.
4. You get the **unified record** — every facility that has data for that NID is
   contacted live (`$everything`) and merged into one tabbed view (Summary /
   Vitals / Labs / Medications / Conditions / Encounters / Immunizations).

### Patient view

1. Open **http://localhost:3000** → tab **Patient**.
2. Login with NID `2345678901` / `patient123` (also `...02`, `...03`).
3. The patient portal shows the same federated bundle in a friendly layout, plus
   Ministry announcements, printable PDF and JSON export.
4. Patients `...09` / `...10` have **no pre-activated account** — demonstrate the
   **self-activation** flow instead: Patient tab → activate with their NID + DOB
   (see table below).

### Ministry / Analytics view

Login as Ministry `superadmin` / `admin123` → **National Analytics** tab shows
record totals, top diagnoses, records by province. **Audit Log** shows every
SEARCH / FETCH_ALL / FETCH_ONE with the sources contacted.

---

## 2. Patient catalog

### 2.1 Shared patients — the federation stars (records at many facilities)

| NID | Name | DOB | Mediciti | Norvic | Central Lab | Pathlabs | SwasthyaEHR |
|---|---|---|---|---|---|---|---|
| `2345678901` | Ram Bahadur Thapa | 1970-05-12 | ✔ | ✔ | ✔ | ✔ | ✔ |
| `2345678902` | Sita Kumari Sharma | 1988-11-23 | ✔ | ✔ | ✔ | ✔ | ✔ |
| `2345678903` | Hari Prasad Koirala | 1979-02-03 | ✔ | ✔ | ✔ | ✔ | ✔ |
| `2345678909` | Laxmi Maya Tamang | 1993-04-14 | ✔ | ✔ | ✔ | ✔ | — |
| `2345678910` | Kiran Bahadur Limbu | 1985-09-19 | ✔ | ✔ | ✔ | ✔ | — |

The best merge demos: **...01** (4 sources) and the new **...09** (4 sources,
70 resources in the unified bundle).

### 2.2 Facility-only patients

| NID | Name | DOB | Lives at |
|---|---|---|---|
| `2345678904` | Gita Devi Rai | 1996-07-19 | Mediciti (and SwasthyaEHR) — dengue + typhoid |
| `2345678905` | Bikash Shrestha | 1962-01-30 | Mediciti only — CKD + heart failure |
| `2345678906` | Maya Gurung | 1975-10-08 | Mediciti only — Hep B / cirrhosis / TB |
| `2345678907` | Deepak Tamang | 1965-09-17 | Norvic only — aortic valve replacement + immunizations |
| `2345678908` | Anjali Pradhan | 1992-12-05 | Norvic only — travel clinic + minor surgery |

### 2.3 Clinical highlights per patient

**Ram (…01)** — Type 2 diabetes → diabetic nephropathy → anemia (4-date HbA1c
trend at Mediciti; creatinine series 1.2→1.9); cardiac work-up at Norvic (CAD);
Lipid/Diabetic profile series at Central; Renal + Coagulation + Viral markers at
Pathlabs. Penicillin allergy.

**Sita (…02)** — hypertension + hypothyroidism + asthma; 3-date TSH trend; CBC
series (anemia) + Iron studies at Central; electrolytes, urine, stool at
Pathlabs.

**Hari (…03)** — IHD + MI + heart failure at Mediciti; PCI (procedure) at
Norvic; Cardiac markers (D-Dimer trend) + febrile panels (scrub typhus +ve) at
Central; dengue panel +ve at Pathlabs.

**Laxmi (…09)** — NEW: asthma + allergic rhinitis and subclinical
hypothyroidism at Mediciti; pre-marriage work-up + anemia + Td/flu vaccines at
Norvic; thyroid series + CBC + iron studies at Central; wellness panels
(electrolytes, urine, vitamins) at Pathlabs. Penicillin allergy.

**Kiran (…10)** — NEW: newly-diagnosed type 2 diabetes + obesity + HTN and a
hypokalemia emergency visit at Mediciti; cardiology assessment (atypical chest
pain) at Norvic; 3-date HbA1c improving series + lipids + renal at Central;
pre-procedure screening (CBC, viral markers, coagulation) at Pathlabs. Contrast
dye allergy.

**Gita (…04)** — dengue (platelet count series 95→62→110) and typhoid
(positive Widal).

**Bikash (…05)** — CKD stage 3 → 5 (eGFR 38→30→24), heart failure, UTI.

**Maya (…06)** — chronic Hep B + cirrhosis (3-date LFT series), TB + pneumonia,
PUD.

**Deepak (…07)** — severe aortic stenosis → mechanical AVR; INR follow-up series;
PCV13 + flu immunizations.

**Anjali (…08)** — travel clinic: Hep A + Typhoid + COVID immunizations,
sebaceous cyst excision.

---

## 3. Access the raw data

### 3.1 Direct FHIR (read-only, API-key guarded)

| Facility | FHIR base | API key |
|---|---|---|
| Nepal Mediciti Hospital | http://localhost:8003/fhir | `mediciti-demo-key-0001` |
| Norvic International | http://localhost:8004/fhir | `norvic-demo-key-0002` |
| Central Diagnostic Lab | http://localhost:9001/fhir | `central-demo-key-0003` |
| Pathlabs Nepal | http://localhost:9002/fhir | `pathlabs-demo-key-0004` |

Example (use single quotes — PowerShell expands `$`):

```powershell
curl.exe -s -H "X-API-Key: mediciti-demo-key-0001" 'http://localhost:8003/fhir/$everything?patient=2345678909'
curl.exe -s -H "X-API-Key: norvic-demo-key-0002"  'http://localhost:8004/fhir/Patient?patient=2345678901'
curl.exe -s -H "X-API-Key: central-demo-key-0003" 'http://localhost:9001/fhir/DiagnosticReport?patient=2345678910'
curl.exe -s -H "X-API-Key: pathlabs-demo-key-0004" 'http://localhost:9002/fhir/DiagnosticReport?patient=2345678909'
```

Per-resource endpoints: `Patient`, `Encounter`, `Condition`, `Observation`,
`AllergyIntolerance`, `MedicationRequest`, `DiagnosticReport`,
`Immunization` (Norvic only), `Procedure` (Norvic only), plus `$everything`.

### 3.2 National platform

| Endpoint (via portal) | What |
|---|---|
| Ministry → Analytics | metadata aggregates: total records (≈492 indexed), patients (11), top diagnoses, province split |
| Ministry → Audit Log | every access with actor, NID, action, sources |
| Doctor search | unified cross-facility bundle |

Platform API base: http://localhost:8000 — login + JWT flow used by the portal.

### 3.3 Databases directly

| DB | Host port | DB name | User / pass | Engine |
|---|---|---|---|---|
| national_db | 5437 | national_db | nuhrs / nuhrs | PostgreSQL |
| mediciti_db | 5438 | mediciti_db | nuhrs / nuhrs | PostgreSQL |
| norvic_db | 5439 | norvic_db | nuhrs / nuhrs | PostgreSQL |
| swastha_db | 5436 | swastha_db | nuhrs / nuhrs | PostgreSQL |
| lab_a_db | 5435 | lab_a_db | nuhrs / nuhrs | PostgreSQL |
| lab_b_db | 3307 | lab_b_db | nuhrs / nuhrs | MySQL |

Pre-configured pgAdmin connections: `pgadmin-servers.json` in the repo root.
Reconnect after seeding (containers keep the same ports).

### 3.4 Quick integrity commands

```bash
# per-service FHIR validity (counts + 0 problems)
docker compose exec mediciti-hospital        python manage.py validate_fhir
docker compose exec norvic-hospital          python manage.py validate_fhir
docker compose exec central-diagnostic-lab   python manage.py validate_fhir
docker compose exec pathlabs-nepal           python manage.py validate_fhir

# platform index health
docker compose exec national-platform python manage.py shell -c "from core.models import RecordIndex, PatientIdentity; print('patients:', PatientIdentity.objects.count()); print('records:', RecordIndex.objects.count())"
```

---

## 4. How to rebuild / reseed (never breaks anything)

All seeds are **idempotent** (upsert by natural key). Re-running is safe and
updates rows in place instead of duplicating.

```bash
docker compose up -d --build            # rebuild images with seed code changes
docker compose exec mediciti-hospital        python manage.py seed
docker compose exec norvic-hospital          python manage.py seed
docker compose exec central-diagnostic-lab   python manage.py seed
docker compose exec pathlabs-nepal           python manage.py seed
```

SwasthyaEHR seeds itself at container start (`seed_demo` + `nuhrs_push`).
Since the automation update, SwasthyaEHR also **indexes live**: every new
diagnosis / lab result / prescription is pushed to the national platform
immediately via `post_save` signals (`core/signals.py` → `core/nuhrs_publish.py`),
so a newly registered patient becomes visible in NUHRS the moment their first
clinical record is saved — no manual push needed. `nuhrs_push --nid <NID>` still
works as a manual backfill.
The national platform bootstraps itself (`superadmin`, 5 orgs, demo users).

---

## 5. Notes & gotchas

- `2345678901/02/03` have pre-activated patient accounts (`patient123`).
- `...09` and `...10` intentionally have **no account yet** — use them for the
  self-activation demo (NID + DOB match ⇒ account created). They already have
  full records at all 4 hospitals/labs, so after activation their portal is rich.
- Allergies exist for Ram, Hari, Maya (Mediciti), Laxmi, Kiran, Anjali, and
  Norvic duplicates — only some patients have them by design.
- Only Norvic produces Immunizations + Procedures (variant-B-only services).
- The platform stores **metadata only** — clinical detail always comes from the
  originating facility at fetch time.
