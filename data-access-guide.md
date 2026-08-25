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
| `2345678927` | Krishna Bahadur Khadka | 1966-12-01 | ✔ | ✔ | ✔ | ✔ | — |
| `2345678915` | Prakash Bahadur Magar | 1963-11-27 | ✔ | ✔ | ✔ | — | — |
| `2345678911` | Bishnu Prasad Ghimire | 1968-03-22 | ✔ | — | ✔ | ✔ | — |
| `2345678919` | Dipendra Bhandari | 1971-07-08 | ✔ | — | ✔ | ✔ | — |
| `2345678925` | Manoj Kumar Tamang | 1976-03-11 | ✔ | — | ✔ | ✔ | — |
| `2345678928` | Rekha Devi Mishra | 1972-05-07 | ✔ | — | — | ✔ | ✔ |
| `2345678912` | Kamala Devi Bhattarai | 1974-08-15 | ✔ | — | ✔ | — | ✔ |
| `2345678918` | Mina Kumari Adhikari | 1986-12-12 | ✔ | — | ✔ | — | ✔ |
| `2345678922` | Sabina Karki | 1992-10-03 | ✔ | — | ✔ | — | ✔ |
| `2345678930` | Bimala Thapa Chhetri | 1997-03-28 | ✔ | — | ✔ | — | ✔ |

The best merge demos: **…27** and **…01** (4 sources each), then **…09** /
**…10** / **…15**.

### 2.2 Facility-only patients

| NID | Name | DOB | Lives at |
|---|---|---|---|
| `2345678904` | Gita Devi Rai | 1996-07-19 | Mediciti (and SwasthyaEHR) — dengue + typhoid |
| `2345678905` | Bikash Shrestha | 1962-01-30 | Mediciti only — CKD + heart failure |
| `2345678906` | Maya Gurung | 1975-10-08 | Mediciti only — Hep B / cirrhosis / TB |
| `2345678907` | Deepak Tamang | 1965-09-17 | Norvic only — aortic valve replacement + immunizations |
| `2345678908` | Anjali Pradhan | 1992-12-05 | Norvic only — travel clinic + minor surgery |
| `2345678913` | Suresh Maharjan | 1982-06-30 | Mediciti + Central — dyslipidemia + NAFLD |
| `2345678914` | Radha Kumari Yadav | 1990-01-09 | Mediciti + Pathlabs — dengue + thrombocytopenia |
| `2345678916` | Sarita Chaudhary | 1995-05-18 | Mediciti + Pathlabs — typhoid + anemia |
| `2345678917` | Nabin Kumar Shah | 1978-09-05 | Mediciti + Pathlabs — Hep B → cirrhosis |
| `2345678920` | Anita Rai Subba | 1998-02-25 | Mediciti + Norvic — asthma + travel clinic |
| `2345678921` | Gopal Krishna Neupane | 1960-04-16 | Mediciti + Norvic — COPD + cor pulmonale |
| `2345678923` | Rajesh Basnet | 1985-01-21 | Norvic only — aortic stenosis → AVR, INR series |
| `2345678924` | Puja Sharma Poudel | 1993-06-14 | Norvic + Central — postpartum anemia |
| `2345678926` | Sunita Lama | 1989-08-29 | Mediciti + Pathlabs — UTI + anemia |
| `2345678929` | Ashok Gurung | 1981-10-19 | Mediciti + Pathlabs — Hep C, cured on DAA |

### 2.3 Patient portal activation cheat-sheet

Values to type at **Portal → Patient → Activate your account**
(`/activate`). NID + DOB are always verified; phone is only checked if you
type one, so you can leave it blank. Password must satisfy the policy:
8+ chars with upper, lower, digit and special (e.g. `Str0ng#Pass`).

| NIN | DOB | Phone (optional) | Name |
|---|---|---|---|
| `2345678901` | 1970-05-12 | `9841000001` | Ram Bahadur Thapa |
| `2345678902` | 1988-11-23 | `9803000002` | Sita Kumari Sharma |
| `2345678903` | 1979-02-03 | `9841000003` | Hari Prasad Koirala |
| `2345678904` | 1996-07-19 | `9812000004` | Gita Devi Rai |
| `2345678905` | 1962-01-30 | `9856000005` | Bikash Shrestha |
| `2345678906` | 1975-10-08 | `9846000006` | Maya Gurung |
| `2345678909` | 1993-04-14 | `9842000001` | Laxmi Maya Tamang |
| `2345678910` | 1985-09-19 | `9842000002` | Kiran Bahadur Limbu |
| `2345678911` | 1968-03-22 | `9841000011` | Bishnu Prasad Ghimire |
| `2345678912` | 1974-08-15 | `9841000012` | Kamala Devi Bhattarai |
| `2345678913` | 1982-06-30 | `9841000013` | Suresh Maharjan |
| `2345678914` | 1990-01-09 | `9841000014` | Radha Kumari Yadav |
| `2345678915` | 1963-11-27 | `9841000015` | Prakash Bahadur Magar |
| `2345678916` | 1995-05-18 | `9841000016` | Sarita Chaudhary |
| `2345678917` | 1978-09-05 | `9841000017` | Nabin Kumar Shah |
| `2345678918` | 1986-12-12 | `9841000018` | Mina Kumari Adhikari |
| `2345678919` | 1971-07-08 | `9841000019` | Dipendra Bhandari |
| `2345678920` | 1998-02-25 | `9841000020` | Anita Rai Subba |
| `2345678921` | 1960-04-16 | `9841000021` | Gopal Krishna Neupane |
| `2345678922` | 1992-10-03 | `9841000022` | Sabina Karki |
| `2345678923` | 1985-01-21 | `9841000023` | Rajesh Basnet |
| `2345678924` | 1993-06-14 | `9841000024` | Puja Sharma Poudel |
| `2345678925` | 1976-03-11 | `9841000025` | Manoj Kumar Tamang |
| `2345678926` | 1989-08-29 | `9841000026` | Sunita Lama |
| `2345678927` | 1966-12-01 | `9841000027` | Krishna Bahadur Khadka |
| `2345678928` | 1972-05-07 | `9841000028` | Rekha Devi Mishra |
| `2345678929` | 1981-10-19 | `9841000029` | Ashok Gurung |
| `2345678930` | 1997-03-28 | `9841000030` | Bimala Thapa Chhetri |

> Pre-activated logins already exist for `...01 / ...02 / ...03`
> (username = NIN, password `patient123`) — activation is only needed for the rest.

### 2.4 Clinical highlights per patient

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

### 2.5 Expanded cohort highlights (…11 – …30)

**Krishna (…27)** — the richest merge: T2DM since 2014 with a 4-date HbA1c
series 9.6→7.2 and lipids 268→196 at Mediciti/Central, CAD work-up + flu vaccine
at Norvic, diabetic nephropathy (creatinine 1.2→1.5, proteinuria) at Pathlabs.

**Prakash (…15)** — inferior STEMI in 2021 → **PCI with drug-eluting stent** at
Norvic, then ischemic heart failure at Mediciti (NT-proBNP 720→1240, hyponatremia)
with lipids driven to target at Central. PCV13 + flu immunizations.

**Bishnu (…11)** — T2DM → diabetic nephropathy: HbA1c 8.9→7.4 alongside
creatinine 1.3→1.7 and eGFR 68→50; urine protein 2+ and negative viral screen at
Pathlabs.

**Dipendra (…19)** — CKD stage 3 progressing over 3 dates (creatinine 1.8→2.2→2.7,
eGFR 44→27) with anemia worsening in step (Hb 10.2→9.3), gout, and hyperkalemia.

**Manoj (…25)** — endemic **scrub typhus** (IgM +ve, CRP 96) with AKI that
resolves: creatinine 2.4→1.3, sodium 128→137, transaminases falling.

**Radha (…14)** — dengue NS1 + IgM positive with the classic platelet dip and
recovery: 88→54→142 across three dates.

**Nabin (…17)** — chronic hepatitis B → cirrhosis: bilirubin 1.4→3.1, albumin
3.9→2.7, INR 1.4→1.7, platelets 82.

**Ashok (…29)** — hepatitis C cured on sofosbuvir/velpatasvir: ALT 112→38 and
platelets 112→168, with Anti-HCV still reactive (antibody persists).

**Rajesh (…23)** — Norvic-only: bicuspid **aortic valve replacement** with a
warfarin INR titration series 1.0→1.8→2.7.

**Sarita (…16)** — enteric fever: Widal 1:320 + Typhidot IgM positive, *S. typhi*
on culture, anemia recovering after ceftriaxone. Sulfonamide allergy.

**Suresh (…13)** — dyslipidemia + NAFLD improving together on rosuvastatin:
LDL 178→112 while ALT 86→52. Penicillin allergy.

**Gopal (…21)** — COPD → cor pulmonale with secondary polycythemia (Hct 50→53)
and an exacerbation with pneumonia; Norvic confirmed pulmonary hypertension.

**Sunita (…26)** — UTI with *E. coli* on culture: pyuria 30-40/hpf clearing to
2-3/hpf after nitrofurantoin, plus iron deficiency.

**Kamala (…12)**, **Mina (…18)**, **Sabina (…22)**, **Rekha (…28)**,
**Bimala (…30)** — the SwasthyaEHR-linked group: hypothyroidism with TSH
normalizing (11.4→3.1), controlled hypertension, PCOS with vitamin D 14→36,
hypertensive CKD (creatinine 1.2→1.6), and young-adult anemia Hb 10.4→12.2.

**Anita (…20)** — asthma + allergic rhinitis at Mediciti, pre-travel Hep A /
Typhoid / Td vaccines at Norvic. Penicillin allergy.

**Puja (…24)** — Norvic-only patient whose postpartum anemia work-up lives at
Central: Hb 9.4→11.8 with ferritin 7→42.

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
| Ministry → Analytics | metadata aggregates: total records (≈1409 indexed), patients (32), top diagnoses, province split |
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

# cross-facility seed invariants: canonical demographics per NID + every lab
# analyte/panel name resolvable in the shared catalog (no Django needed)
python tools/check_seed_consistency.py

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
  The whole `...11`–`...30` cohort is also account-free for the same reason —
  `...27` is the best one to activate (records at all four facilities).
- Allergies exist for Ram, Hari, Maya (Mediciti), Laxmi, Kiran, Anjali, plus
  Suresh (…13), Sarita (…16) and Anita (…20) in the expanded cohort, and the
  Norvic duplicates — only some patients have them by design.
- Only Norvic produces Immunizations + Procedures (variant-B-only services).
  In the expanded cohort that means the PCI (…15) and the AVR (…23).
- Facility coverage varies on purpose: some patients sit at one facility, some at
  four. `tools/check_seed_consistency.py` prints the full per-NID coverage map.
- The platform stores **metadata only** — clinical detail always comes from the
  originating facility at fetch time.
