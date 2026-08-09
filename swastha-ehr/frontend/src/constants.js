// Frontend copies of backend vocabularies (v2). The backend re-validates
// everything; these drive dropdowns/labels. Big catalogs (lab tests, ICD-10,
// departments) are fetched live from the API instead of hardcoded here.

export const GENDER_OPTIONS = [
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "other", label: "Other" },
  { value: "unknown", label: "Unknown" },
];

export const BLOOD_GROUPS = [
  "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "UNKNOWN",
];

export const MARITAL_STATUS = [
  { value: "", label: "—" },
  { value: "SINGLE", label: "Single" },
  { value: "MARRIED", label: "Married" },
  { value: "DIVORCED", label: "Divorced" },
  { value: "WIDOWED", label: "Widowed" },
  { value: "OTHER", label: "Other" },
];

// Clinical staff roles that can self-register (admin/patient cannot).
export const STAFF_ROLES = [
  { value: "RECEPTIONIST", label: "Receptionist" },
  { value: "NURSE", label: "Nurse" },
  { value: "DOCTOR", label: "Doctor" },
  { value: "LAB_TECH", label: "Laboratory Technician" },
  { value: "PHARMACIST", label: "Pharmacist" },
];

// The 7 departments (also fetched from /api/v1/departments/ for freshness).
export const DEPARTMENTS = [
  { value: "ENDOCRINOLOGY", label: "Diabetes & Endocrinology" },
  { value: "INTERNAL_MEDICINE", label: "Internal Medicine" },
  { value: "NEPHROLOGY", label: "Nephrology" },
  { value: "CARDIOLOGY", label: "Cardiology" },
  { value: "GASTROENTEROLOGY", label: "Gastroenterology / Hepatobiliary" },
  { value: "INFECTIOUS_DISEASES", label: "Infectious Diseases" },
  { value: "HEMATOLOGY", label: "Hematology" },
];

export const ENCOUNTER_STATUS_LABELS = {
  REGISTERED: "Registered",
  VITALS_DONE: "Vitals recorded",
  WITH_DOCTOR: "With doctor",
  LAB_PENDING: "Awaiting lab",
  LAB_DONE: "Lab complete",
  CLOSED: "Closed",
};

// Where each role lands after login.
export const ROLE_HOME = {
  ADMIN: "/admin",
  DOCTOR: "/doctor",
  RECEPTIONIST: "/reception",
  NURSE: "/nurse",
  PHARMACIST: "/pharmacy",
  LAB_TECH: "/lab",
  PATIENT: "/portal",
};

// Per-role visual theme for the dashboard chrome. Badges/rings are tuned for
// the light NUHRS surfaces; role identity is expressed through small badges
// and rings only — surfaces, buttons and layout stay shared and neutral.
export const ROLE_THEME = {
  ADMIN: { label: "Administrator", badge: "bg-slate-500/10 text-slate-700 ring-1 ring-slate-500/40", ring: "ring-slate-500/30" },
  DOCTOR: { label: "Consultation Room", badge: "bg-blue-500/10 text-blue-700 ring-1 ring-blue-500/40", ring: "ring-blue-500/30" },
  RECEPTIONIST: { label: "Front Desk", badge: "bg-amber-500/10 text-amber-700 ring-1 ring-amber-500/40", ring: "ring-amber-500/30" },
  NURSE: { label: "Nursing Station", badge: "bg-rose-500/10 text-rose-700 ring-1 ring-rose-500/40", ring: "ring-rose-500/30" },
  PHARMACIST: { label: "Dispensing Window", badge: "bg-emerald-500/10 text-emerald-700 ring-1 ring-emerald-500/40", ring: "ring-emerald-500/30" },
  LAB_TECH: { label: "Diagnostic Lab", badge: "bg-violet-500/10 text-violet-700 ring-1 ring-violet-500/40", ring: "ring-violet-500/30" },
  PATIENT: { label: "Patient Portal", badge: "bg-brand-500/10 text-brand-700 ring-1 ring-brand-500/40", ring: "ring-brand-500/30" },
};

export const DEFAULT_THEME = {
  label: "Workspace",
  badge: "bg-brand-500/10 text-brand-700 ring-1 ring-brand-500/40",
  ring: "ring-brand-500/30",
};


