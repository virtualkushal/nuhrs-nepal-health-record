# NIN Reference — NUHRS 10-digit National Identification Number

Nepal's official **National Identification Number (NIN)**, issued by the
Department of National ID and Civil Registration (DoNIDCR) under the National
Identity Card and Registration Act, 2076, is **exactly 10 digits**. It is
non-intelligible (no meaning encoded in the digits) and carries **no checksum**,
so every NUHRS service validates strictly on format.

This document records the migration from the previous (incorrect) 11-digit
assumption, and is the single cheat-sheet for reaching every seeded record.

---

## 1. OLD → NEW NIN mapping

### Mapping rule

```
new_NIN = old_11_digit_NID with its LEADING digit dropped
        = old[1:]

12345678901  ->  2345678901
```

One uniform, deterministic transformation applied to **every** seed file. Every
seeded NID began with `1`, so the result is always exactly 10 digits and remains
collision-free because the patients differ in their trailing digits. The
cross-service "`...901 / 902 / 903` MUST match" pairings are therefore
preserved — they simply now read `2345678901 / 02 / 03` everywhere. The rule is
documented in the header comment of each seed file.

### Patient mapping table

| OLD NID (11) | NEW NIN (10) | Patient name | DOB | Present in |
|---|---|---|---|---|
| `12345678901` | `2345678901` | Ram Bahadur Thapa | 1970-05-12 | National index · Mediciti · Norvic · Central Lab · Pathlabs · SwasthyaEHR |
| `12345678902` | `2345678902` | Sita Kumari Sharma | 1988-11-23 | National index · Mediciti · Norvic · Central Lab · Pathlabs · SwasthyaEHR |
| `12345678903` | `2345678903` | Hari Prasad Koirala | 1979-02-03 | National index · Mediciti · Norvic · Central Lab · Pathlabs · SwasthyaEHR |
| `12345678904` | `2345678904` | Gita Devi Rai | 1996-07-19 (Mediciti) · 2001-07-19 (SwasthyaEHR) | Mediciti · SwasthyaEHR |
| `12345678905` | `2345678905` | Bikash Shrestha | 1962-01-30 | Mediciti |
| `12345678906` | `2345678906` | Maya Gurung | 1975-10-08 | Mediciti |
| `12345678907` | `2345678907` | Deepak Tamang | 1965-09-17 | Norvic |
| `12345678908` | `2345678908` | Anjali Pradhan | 1992-12-05 | Norvic |
| `12345678909` | `2345678909` | Laxmi Maya Tamang | 1993-04-14 | Mediciti · Norvic · Central Lab · Pathlabs |
| `12345678910` | `2345678910` | Kiran Bahadur Limbu | 1985-09-19 | Mediciti · Norvic · Central Lab · Pathlabs |

> The `2345678904` DOB differs between Mediciti (1996-07-19) and SwasthyaEHR
> (2001-07-19). That mismatch pre-existed this migration and was left untouched —
> only the ID digits changed.

Non-patient literal also migrated: the unit-test placeholder NID in
`national-platform/core/tests.py` went `11112222333` → `1112222333`.

Demographics, DOBs, genders, phones, diagnoses, encounters, vitals, labs,
medications, immunizations, procedures, users and roles are **unchanged**.

---

## 2. Access cheat-sheet

Every record is reachable exactly as before — only the ID digits changed.

### 2.1 Patients — national portal (http://localhost:3000 → Patient tab)

Pre-activated accounts (username = NIN):

| NIN | Patient | Password |
|---|---|---|
| `2345678901` | Ram Bahadur Thapa | `patient123` |
| `2345678902` | Sita Kumari Sharma | `patient123` |
| `2345678903` | Hari Prasad Koirala | `patient123` |

Self-activation (NIN + DOB, you choose the password). Use these two — they
deliberately have **no** pre-activated account but rich records at all four
hospitals/labs:

| NIN | Patient | DOB to enter | Phone on file |
|---|---|---|---|
| `2345678909` | Laxmi Maya Tamang | `1993-04-14` | `9842000001` |
| `2345678910` | Kiran Bahadur Limbu | `1985-09-19` | `9842000002` |

The activation form now enforces the password policy in §3, so pick something
like `Str0ng#Pass`. Phone is optional; when supplied it must match the value on
file and satisfy the Nepal mobile rule.

### 2.2 Doctors — per hospital (scope **Staff**)

Log in with scope `Staff`, the organization code, login name `doctor`:

| Facility | Org code | Login name | Password | Full username |
|---|---|---|---|---|
| Nepal Mediciti Hospital | `HOSP001` | `doctor` | `doctor123` | `HOSP001-DOC-0001` |
| Norvic International Hospital | `HOSP002` | `doctor` | `doctor123` | `HOSP002-DOC-0001` |
| SwasthyaEHR Hospital | `HOSP003` | `doctor` | `doctor123` | `HOSP003-DOC-0001` |
| Central Diagnostic Laboratory | `LAB001` | `doctor` | `doctor123` | `LAB001-DOC-0001` |
| Pathlabs Nepal | `LAB002` | `doctor` | `doctor123` | `LAB002-DOC-0001` |

Organization admins (same scope, login name `admin`):

| Org code | Login name | Password | Full username |
|---|---|---|---|
| `HOSP001` … `LAB002` | `admin` | `org123` | `<ORG>-ADM-0001` |

### 2.3 Super Admin / Ministry

| Role | Scope | Username | Password |
|---|---|---|---|
| Super Admin (Ministry) | `MINISTRY` | `superadmin` | `admin123` |

The Ministry view exposes the Provider Registry, user management,
announcements, National Analytics and the Audit Log.

### 2.4 SwasthyaEHR standalone app (http://localhost:3090, login by **email**)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@demo.np` | `demo12345` |
| Receptionist | `reception@demo.np` | `demo12345` |
| Nurse | `nurse@demo.np` | `demo12345` |
| Doctor (Endocrinology) | `doctor@demo.np` | `demo12345` |
| Doctor (Cardiology) | `doctor2@demo.np` | `demo12345` |
| Doctor (Infectious Diseases) | `doctor3@demo.np` | `demo12345` |
| Lab technician | `labtech@demo.np` | `demo12345` |
| Pharmacist | `pharmacist@demo.np` | `demo12345` |
| Patient portal (Ram) | `ram@demo.np` | `demo12345` |
| Patient portal (Gita) | `gita@demo.np` | `demo12345` |
| Bootstrap admin (`seed_admin`) | `admin@swasthya.org.np` | `admin12345` |

### 2.5 Organization API keys (federation endpoints — unchanged)

| Facility | Org code | API key | FHIR base URL |
|---|---|---|---|
| Nepal Mediciti Hospital | `HOSP001` | `mediciti-demo-key-0001` | `http://mediciti-hospital:8003/fhir` |
| Norvic International Hospital | `HOSP002` | `norvic-demo-key-0002` | `http://norvic-hospital:8004/fhir` |
| SwasthyaEHR Hospital | `HOSP003` | `swastha-demo-key-0005` | `http://swastha-backend:8090/fhir` |
| Central Diagnostic Laboratory | `LAB001` | `central-demo-key-0003` | `http://central-diagnostic-lab:9001/fhir` |
| Pathlabs Nepal | `LAB002` | `pathlabs-demo-key-0004` | `http://pathlabs-nepal:9002/fhir` |

Sent as the `X-API-Key` header. Example — fetch a unified record by NIN:

```bash
curl -H "X-API-Key: mediciti-demo-key-0001" \
     "http://localhost:8003/fhir/Patient/2345678901/\$everything"
```

### 2.6 Demo password compliance note

The seeded demo passwords above (`admin123`, `org123`, `doctor123`,
`patient123`, `demo12345`, `admin12345`) do **not** satisfy the policy in §3.
They were deliberately left unchanged so every existing demo script, screenshot
and walkthrough keeps working. The policy is enforced on **new** credentials:
account creation, password changes, resets and patient self-activation. Do not
use these values outside the local demo.

---

## 3. Validation rules (quick reference)

### 3.1 National Identification Number (NIN)

| | |
|---|---|
| Regex | `^\d{10}$` |
| Normalization | spaces and hyphens stripped before matching (`2345-678 901` → `2345678901`) |
| Error message | `National ID must be exactly 10 digits (Nepal NIN).` |
| Rationale | DoNIDCR NIN: 10 digits, non-intelligible, no checksum |

Enforced in:
- `national-platform/core/validators.py` (`NID_RE`, `validate_nid`, `is_valid_nid`)
- `mediciti-hospital/clinical/validators.py`
- `norvic-hospital/clinical/validators.py`
- `central-diagnostic-lab/lab/validators.py`
- `pathlabs-nepal/lab/validators.py`
- `swastha-ehr/backend/core/serializers.py` (`NID_RE`)
- Frontend mirrors: `frontend-react/src/lib/validation.js` (`NIN_PATTERN`),
  `swastha-ehr/frontend/src/components/PatientForm.jsx`

No database migration was required — NIN is a validated string field.

### 3.2 Nepal mobile number

| | |
|---|---|
| Regex | `^(\+977\|00977\|0)?9[678]\d{8}$` |
| Accepted input | `9841234567`, `+9779841234567`, `009779841234567`, `09841234567`, and forms with spaces/hyphens/parens |
| Stored form | bare 10 digits — the `+977` / `00977` / `0` prefix is stripped on normalization |
| Coverage | NTC (`984/985/986`, `974/975`), Ncell (`980/981/982`, `970/971`), Smart Cell (`961/962`, `988`) |
| Error message | `Enter a valid Nepal mobile number, e.g. 9841234567 or +9779841234567.` |

Shared constant name `NEPAL_MOBILE_RE` in every backend validators module and in
`swastha-ehr/backend/core/serializers.py`; mirrored in the frontends as
`NEPAL_MOBILE_PATTERN`. Applied to patient phone numbers, emergency contact
phones, staff phones and patient self-registration.

### 3.3 Password policy

| | |
|---|---|
| Regex | `^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$` |
| Rules | min 8 chars · ≥1 uppercase · ≥1 lowercase · ≥1 digit · ≥1 special |
| Example valid | `Str0ng#Pass` |

Implemented Django-natively as
`core.password_validation.NuhrsPasswordPolicyValidator` and registered in
`AUTH_PASSWORD_VALIDATORS` for both the national platform and SwasthyaEHR,
alongside `MinimumLengthValidator(min_length=8)`. Serializer- and view-level
checks call the same rule so DRF endpoints return clean field errors:

- national platform: change password, patient self-activation, patient self-registration
- SwasthyaEHR: admin-created staff, change password, password-reset confirm

Auto-generated temporary passwords (`services.generate_temp_password`,
`_generate_password`) now always satisfy the policy.
