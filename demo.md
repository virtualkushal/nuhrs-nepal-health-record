# NUHRS — Live Demo Script (for Supervisor)

A step-by-step walkthrough of **NUHRS — National Unified Health Record System**,
a prototype Federated Health Information Exchange (HIE) for Nepal built on
**HL7 FHIR R4**.

The goal of this demo is to prove four things:

1. **Data sovereignty** — hospitals/labs keep their own data; the National
   Platform stores only pointers (metadata), never clinical records.
2. **Interoperability** — one patient's records can be unified across facilities
   even though each facility uses a *different* internal schema and even a
   *different database engine*.
3. **Governance** — the Ministry can register/approve/suspend facilities and
   every cross-organization access is written to an immutable audit log.
4. **Accessibility** — doctors and patients each get a portal: doctors get the
   full clinical view, patients get a friendly personal health record.

---

## 0. Before the meeting

Checklist — everything should be running **before** the supervisor joins:

```bash
# 1. Start everything
docker compose up -d --build

# 2. Seed clinical data (all seeds are idempotent; re-running is safe)
./seed-all.sh

# 3. (Optional) clean up any stale services from older compose versions
docker compose up -d --remove-orphans
```

Note: `seed-all.sh` only seeds Mediciti, Norvic, Central Diagnostic Lab and
Pathlabs. The National Platform auto-bootstraps itself (Super Admin + the five
demo organizations) and SwasthyaEHR seeds + self-registers with the platform at
startup, so **nothing extra is needed for those two**.

Verify everything is healthy:

```bash
docker compose ps
```

| Service | Port | URL |
|---|---|---|
| National Frontend (portal) | 3000 | http://localhost:3000 |
| SwasthyaEHR SPA | 3090 | http://localhost:3090 |
| National Platform API | 8000 | http://localhost:8000 |
| Mediciti FHIR | 8003 | http://localhost:8003/fhir/{resource} |
| Norvic FHIR | 8004 | http://localhost:8004/fhir/{resource} |
| Central Diagnostic Lab FHIR | 9001 | http://localhost:9001/fhir/{resource} |
| Pathlabs FHIR | 9002 | http://localhost:9002/fhir/{resource} |
| SwasthyaEHR API | 8090 | http://localhost:8090 |

---

## Architecture in one slide (say this out loud)

We run a real federation on the demo machine, in Docker:

- **National Platform** (`national-platform/`) — Django. Master Patient Index
  (MPI), Provider Registry, Record Index, JWT auth + org API keys, audit log,
  and the **Routing Engine**. It contains **zero clinical tables**.
- **5 edge organizations**, each an independent app with its own database and
  its own **FHIR adapter** that maps their private schema to identical
  HL7 FHIR R4 output:
  - Mediciti (HOSP001, PostgreSQL, "schema variant A")
  - Norvic (HOSP002, PostgreSQL, "variant B" — different column names + extra
    Immunization/Procedure services)
  - SwasthyaEHR (HOSP003, PostgreSQL, own React SPA)
  - Central Diagnostic Lab (LAB001, PostgreSQL)
  - Pathlabs Nepal (LAB002, **MySQL** — proving the adapter is database-engine
    agnostic)
- **2 frontends**: the national React portal (`frontend-react/`) and Swasthya's
  dedicated SPA.

Key mechanics to remember when explaining:

- **NID links a patient everywhere** — the 10-digit Nepal National Identity
  Number is the same in every facility's seed data.
- Edge services push **metadata only** to the platform's `IndexIngestView`
  (record index). Full data is fetched on demand via `GET /fhir/$everything`.
- The Routing Engine in
  `national-platform/core/services.py` reads the Record Index, fans out to each
  organization's `$everything` endpoint, merges the FHIR bundles, tags each
  entry with `_source`, and writes an `AuditLog` row. This *is* the demo's
  headline moment.

---

## Demo Script (10–12 minutes)

### Stage 1 — Ministry / Super Admin view (2 min)

Open **http://localhost:3000** → tab **Ministry**.

**Login:**
| Scope | Username | Password |
|---|---|---|
| Ministry | `superadmin` | `admin123` |

Show the **Super Admin Dashboard** tabs:

1. **Organizations (Provider Registry)** — show the 5 active orgs
   (HOSP001…LAB002) with their license numbers and districts. Explain that in a
   real deployment a facility **registers** (PENDING) and the Ministry
   **approves** — here they are pre-approved/ACTIVE so the demo works
   out-of-the-box. Optionally demo the full flow:
   - Open the **Register a Facility** link on the landing page, fill a fake
     hospital (type HOSPITAL), and watch it appear as **PENDING**.
   - Come back as superadmin and click **Approve** — the UI shows the one-time
     credentials (`ORG CODE`, admin login, temp password, API key) exactly as a
     new org admin would receive them.
   - Then **Suspend** it and note the org disappears from the doctor's login
     dropdown (suspension takes effect at login gate in
     `services.resolve_login_user`).
   - **Reactivate**, or leave suspended.
2. **Users** — filter by role; demonstrate **Reset Password** on one user shows
   a one-time temp password returned once.
3. **Announcements** — click **Publish Announcement** with a public-health
   title ("Free measles-rubella vaccination camp"). We will come back and see it
   in the patient portal.
4. **National Analytics** — this aggregates Record metadata (top diagnoses,
   records by province, total exchanges). Emphasize: this is possible *without*
   the Ministry ever seeing a single clinical value.
5. **Audit Log** — (check this AFTER the doctor stage; you will see the fresh
   SEARCH / FETCH_ALL entries with actor, patient NID and the facilities
   contacted).

**Under the hood:** every tab is a REST call to the platform:
`core/views.py` — provider registry views, `AnalyticsSummaryView`, audit feed.

---

### Stage 2 — Raw FHIR REST (2:00, browser + curl)

Show that the edge services are plain, standards-facing FHIR endpoints. Keep a
terminal open:

```bash
# Mediciti — a Patient named Ram Bahadur Thapa
curl -s "http://localhost:8003/fhir/Patient?patient=2345678901" | head -50

# Central Diagnostic Lab — a DiagnosticReport (lab panel for the same patient)
curl -s "http://localhost:9001/fhir/DiagnosticReport?patient=2345678901" | head -40

# Pathlabs (MySQL engine) — identical FHIR shape
curl -s "http://localhost:9002/fhir/DiagnosticReport?patient=2345678901" | head -40
```

**Key point:** the lab data behind `9001` lives in PostgreSQL and behind `9002`
lives in MySQL — yet both respond with **identical FHIR R4 resource shapes**.
That proves the FHIR adapter abstracts the storage engine.

There is also a per-service validator you can run before the demo:

```bash
docker compose exec mediciti-hospital python manage.py validate_fhir
docker compose exec central-diagnostic-lab python manage.py validate_fhir
```

These assert every seeded patient maps to valid FHIR R4 JSON.

---

### Stage 3 — Doctor: the unified record (the centrepiece, 4 minutes)

Sign out (or open a new tab). Sign in as a **Doctor**:

| Scope | Org Code | Login (login name) | Password |
|---|---|---|---|
| Staff | `HOSP001` | `doctor` | `doctor123` |

(Also works: `HOSP001-DOC-0001` — see bootstrap for the legacy usernames.)

1. Land on the **Doctor Home**: connected facilities list (LIVE), record
   counts, and the central **SEARCH PATIENT bar**.
2. Type the NID **`2345678901`** (Ram Bahadur Thapa) and search.
   Observe "…**Contacting facilities across the network…**".
3. The **Patient Record Exchange** opens the unified record:
   - **Summary** — blood group, active allergies count, diagnosis list,
     most recent lab tests.
   - **Vitals** — trend line chart with every blood pressure / pulse reading
     **from every facility blended into one timeline**.
   - **Lab Reports** — panels from *both* labs (Central Diagnostic + Pathlabs),
     arranged newest-first, each tagged with the source facility.
   - **Medications / Conditions / Encounters** — same cross-source blending.
   - **Immunizations** — *only Norvic produces these* (variant-B-only service);
     show they appear in the same unified record and are absent from Mediciti.
4. Try a second patient **`2345678902`** (Sita Kumari Sharma) to stop any
   "it's all hard-coded" worry.

**What actually happened, to say out loud:**

> The doctor logged in, that is JWT-authenticated. The search called the
> MPI (`GET /patient/2345678901`, writing a SEARCH audit entry). The platform
> then **did not** read a central database — it consulted only the Record
> Index, learned Ram has records in Mediciti, Norvic, Central Diag Lab and
> Pathlabs, then issued parallel `GET /fhir/$everything?patient=…` calls to
> each of those live services, passing each org's API **key**. The FHIR bundles
> came back and were merged into one Bundle. The platform never stored a byte of
> clinical data — it was transient. Every one of those fetches logged a
> FETCH_ALL entry with the URLs contacted.

---

### Stage 4 — a single record — and the audit trail (2 minutes)

1. In the Exchange view click on ONE row (e.g. a single lab report). The
   routing engine execution `fetch_one` returns only that resource.
2. Then go back to **Audit Log** (Ministry tab) and filter by action — you will
   see both `FETCH_ALL` (with `target_orgs`) and individual `FETCH_ONE` entries.

**Under the hood:** `PatientFetchView` in `core/views.py`; `RoutingEngine` in
`core/services.py`; immutability of `AuditLog` in `core/models.py`.

---

### Stage 5 — patient experience (1:30)

In a fresh tab:

| Scope | Username | Password |
|---|---|---|
| Patient | `2345678901` | `patient123` |

1. The **Health Card** loads — blood group, allergies, DoB, last vitals.
2. **Overview bento** — Care Summary, Recent Visits, Health Journey.
3. **Vitals / Lab Results / Medications / Immunizations** — friendly labels,
   no code. emphasize that this is the *same* federated FHIR bundle the doctor
   sees, but rendered for a layperson.
4. Tab **Health Updates** — you already published an announcement in Stage 1:
   **show it here**. (This proves the two portals talk to the same platform.)
5. **Settings / printable record** — `Save as PDF` (print CSS) and the
   "Download JSON" button — exportability / portability.
6. Then show **self-activation** (optional): using a NID you have *not* yet
   created an account for, fill NID + DOB `1970-05-12` — the backend re-verifies
   against the MPI (DOB + phone) and creates the patient account only if it
   matches. NID `2345678901` is already pre-activated (`patient123`), so
   activating it will show the "already activated" message — use that to
   demonstrate the guard, then a brand-new NID to demonstrate the success path.

**Under the hood:** the patient bundle uses a *self-scoped* endpoint —
`/api/v1/patient/bundle/` (in `PatientMyBundleView`) where the NID is read from
the authenticated session, never from the request — a patient cannot request
another patient's record.

---

### Stage 6 — a different hospital, a different DB engine (1 min, optional)

Sign in as:

| Scope | Org | Login | Password |
|---|---|---|---|
| Staff | `LAB002` (Pathlabs) | `doctor` | `doctor123` |

The doctor belongs to the MySQL-backed lab. Show that their search UI is
identical and the unified record still aggregates the whole federation — search
a shared NID (`2345678901`) and point out that the platform contacted a
MySQL-backed source as easily as the Postgres ones.

---

### Stage 7 — SwasthyaEHR, a third hospital with its own SPA (2 min, optional)

The showpiece: a **live, zero-hassle write path**. A new patient registered in
SwasthyaEHR becomes part of their National Unified Health Record the moment a
clinical record is saved — no manual sync, no scripts.

**Part 1 — Register in SwasthyaEHR (http://localhost:3090)**

1. Login as Receptionist: `reception@demo.np` / `demo12345`
2. Click **New patient** and register a NEW citizen — pick an 10-digit National
   ID not used anywhere else (e.g. `2345678955`; a reused one is rejected as
   "already exists"). Name, phone, DOB, gender, blood group → **Register
   patient**. Note the hospital ID (e.g. `HOSP-2026-0000X`).
3. Log out → login as Doctor: `doctor@demo.np` / `demo12345`
4. **Check in** the patient (creates the encounter), then add **one diagnosis**
   (e.g. ICD-10 `I10` → "Essential (primary) hypertension").
5. Optional wow: order a lab test, then log in as `labtech@demo.np` and enter a
   result.

**Part 2 — watch it arrive on the National Platform**

1. Open **http://localhost:3000** → tab **Doctor** (`doctor` / `doctor123`).
2. Search the patient's **NID** — the unified record now shows
   **SwasthyaEHR Hospital (HOSP003)** among the sources, with the diagnosis,
   and the citizen is in the national Master Patient Index.

**What happened under the hood (say this out loud):**

> The hospital keeps its data. The moment a diagnosis / lab result / prescription
> is saved, a `post_save` signal pushes only a **metadata pointer** (NID + one
> line summary) to the platform's index. When the national doctor searches the
> NID, the Routing Engine fetches the *actual* record live from Swasthya's FHIR
> adapter over the network. This is the write-path story: **registration +
> first clinical record → discoverable federation-wide, automatically.**

Implementation: `core/signals.py` (post_save → `core/nuhrs_publish.py` →
platform `IndexIngestView`). The `nuhrs_push` management command still exists
as a bulk re-sync/backfill (e.g. after local data edits) and runs at container
startup for the seeded data.

---

### Stage 8 — wrap-up slide (2 min)

- **Punchline:** 5 orgs, 2 DB engines, 2 schema families (A/B), all speaking one
  FHIR R4 dialect through the platform, with a full audit trail and no clinical
  data stored centrally.
- Show the **seed counts** from the terminal: Mediciti — 8 patients, 38
  conditions, 47 lab reports, 37 medications; Norvic — 7 patients, 10
  immunizations, 3 procedures; Central lab — 28 reports; Pathlabs — 19 reports;
  11 citizens in the national MPI, ~492 indexed records. Makes the demo feel
  real. See `data-access-guide.md` for the full patient catalog.

---

## Troubleshooting quick ref (have handy)

| Symptom | Fix |
|---|---|
| `docker compose up` says port already in use (5432/3306/3000…) | A local DB/web server is on that port. Change `ports:` mapping or stop it; all app ports are used in the compose file. |
| Seed says "This seed is for LAB001, not ORG_CODE" | Wrong command run in the wrong service; check service name (`docker compose exec pathlabs-nepal …`, not `lab-b`). |
| Platform shows org offline (OperationOutcome entry) | The edge container restarted; give it 5–10s and refresh. All `$everything` calls include `_source` so a missing org shows "source ... unavailable" rather than crashing. |
| Stale orphan containers from an old compose file | `docker compose up -d --remove-orphans`. |
| Swasthya duplication on repeated seeds | Seeds are idempotent (upsert by natural key); re-running `seed` is safe. |

---

## What's Done (in this prototype / shippable)

- Federated metadata index + routing engine (fetch all / fetch one) — `core/services.py`.
- FHIR R4 adapter per edge service; variant A (MedHosp1 + CentralLab) and
  variant B (Norvic + Pathlabs) with different columns. All emit *identical*
  FHIR for the shared patients.
- Both DB engines exercised (PG + MySQL) end-to-end.
- National portal: Ministry (registry approval/suspend, user mgmt, announcements,
  analytics, audit), Org Admin (staff CRUD), Doctor (unified Exchange, trends,
  per-domain tabs), Patient (friendly portal, export, self-activation).
- Scope-based login (Staff / Patient / Ministry) with org code + login name.
- **Automatic federation write-path**: SwasthyaEHR indexes every new diagnosis /
  lab result / prescription on the national platform instantly via `post_save`
  signals (`core/signals.py` → `core/nuhrs_publish.py`); the `nuhrs_push`
  command remains as a bulk backfill.
- Rich demo data: Nepal-endemic conditions (Typhoid, Dengue, TB, scrub typhus,
  Hepatitis B) + matching lab panels (Widal, Febrile Illness, Viral Markers),
  immunizations & procedures (Norvic only), vitals trends.
- Audit log for every SEARCH / FETCH_ALL / FETCH_ONE.

---

## What is Left / Future Work (candidate roadmap)

Pack for "what's next / what I would do if I continued".

**Correctness & hardening**
- Real OAuth 2.0 / SMART-on-FHIR with consent tuples instead of shared API keys
  (keys today are static demo keys, stored plainly in compose env).
- Consent management for patient-level sharing; today access is granted by
  platform/org admins with no explicit per-lookup patient consent capture.
- TLS (HTTPS) end-to-end; infra-wide secrets management (no committed keys).
- Row-level authorization / policy engine (who can see what resource types per
  org), and RBAC separation of lab tech vs doctor beyond the current role labels.
- Table constraints / indexes tuned, and the analytics endpoint de-identified
  with k-anonymity checks before reuse.

### Interoperability depth
- Write path: SwasthyaEHR publishes metadata automatically on record creation,
  but the wired hospitals/labs still index only at seed time; extend the same
  `post_save` pattern (or their equivalents) across all edge services, and
  broadcast full document-level workflows (referral, discharge summary push) —
  Swasthya's `share/outbound/` exists as a template.
- Upload documents: attachment / PDF reporting pipeline (media is currently
  stubbed — `settings.py` notes "future PDF pipeline", `PDF_EXTRACTED` state
  reserved).
- More FHIR resources (DocumentReference, MedicationRequest overlays, Service
  Request) and deeper ICD-10 / SNOMED-CT terminology; validate the Norvic
  immunization schedules against the national schedule.

### Platform / ops
- Production multi-machine deployment (Kubernetes), failover for platform.
- Observability: structured logs, metrics, tracing on every `$everything` call.
- CI/CD: Django+React tests, Docker build pipelines, DRF API contract tests.
- E2E test suite over the composed stack (playwright) so the demo reliably passes.
- Localization (Nepali), accessibility (WCAG) polish, and a mobile patient flow.

---

### Suggested close

> So the prototype covers the full loop: which data stays where, how it gets
> joined on NID through FHIR, how the Ministry controls and audits, and how both
> the clinic and the citizen get the user experience. The remaining investment
> is mostly around security, consent, and scale — which is the natural next
> phase.