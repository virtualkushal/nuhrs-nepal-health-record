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
// the dark navy surfaces; each role keeps its own accent gradient identity.
export const ROLE_THEME = {
  ADMIN: { label: "Administrator", badge: "bg-slate-500/20 text-slate-200 ring-1 ring-slate-400/30", gradient: "from-slate-500 to-slate-700", ring: "ring-slate-500/30", tint: "from-slate-500/10 to-transparent" },
  DOCTOR: { label: "Consultation Room", badge: "bg-blue-500/20 text-blue-200 ring-1 ring-blue-400/30", gradient: "from-blue-500 to-indigo-600", ring: "ring-blue-500/30", tint: "from-blue-500/10 to-transparent" },
  RECEPTIONIST: { label: "Front Desk", badge: "bg-amber-500/20 text-amber-200 ring-1 ring-amber-400/30", gradient: "from-amber-500 to-orange-600", ring: "ring-amber-500/30", tint: "from-amber-500/10 to-transparent" },
  NURSE: { label: "Nursing Station", badge: "bg-rose-500/20 text-rose-200 ring-1 ring-rose-400/30", gradient: "from-rose-500 to-pink-600", ring: "ring-rose-500/30", tint: "from-rose-500/10 to-transparent" },
  PHARMACIST: { label: "Dispensing Window", badge: "bg-emerald-500/20 text-emerald-200 ring-1 ring-emerald-400/30", gradient: "from-emerald-500 to-green-600", ring: "ring-emerald-500/30", tint: "from-emerald-500/10 to-transparent" },
  LAB_TECH: { label: "Diagnostic Lab", badge: "bg-violet-500/20 text-violet-200 ring-1 ring-violet-400/30", gradient: "from-violet-500 to-purple-600", ring: "ring-violet-500/30", tint: "from-violet-500/10 to-transparent" },
  PATIENT: { label: "Patient Portal", badge: "bg-brand-500/20 text-brand-200 ring-1 ring-brand-400/30", gradient: "from-brand-500 to-brand-800", ring: "ring-brand-500/30", tint: "from-brand-500/10 to-transparent" },
};

export const DEFAULT_THEME = {
  label: "Workspace",
  badge: "bg-brand-500/20 text-brand-200 ring-1 ring-brand-400/30",
  gradient: "from-brand-500 to-brand-800",
  ring: "ring-brand-500/30",
  tint: "from-brand-500/10 to-transparent",
};


