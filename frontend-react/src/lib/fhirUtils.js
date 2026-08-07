// Shared FHIR bundle parsing for the doctor dashboard.
//
// The National Platform returns a `collection` Bundle of raw FHIR R4 resources,
// each tagged with `_source` (the originating hospital/lab). Lab panels arrive
// as a DiagnosticReport plus SEPARATE top-level laboratory Observations linked
// by `result[].reference` -> `Observation/labresult-<id>` (NOT `contained`).
// Every tab reads through these helpers so parsing lives in exactly one place.

const resourcesOf = (bundle, type) =>
  (bundle?.entry || [])
    .map((e) => e.resource)
    .filter((r) => r && r.resourceType === type);

export const extractPatient = (b) => resourcesOf(b, "Patient")[0] || null;
export const extractAllergies = (b) => resourcesOf(b, "AllergyIntolerance");
export const extractMedications = (b) => resourcesOf(b, "MedicationRequest");
export const extractImmunizations = (b) => resourcesOf(b, "Immunization");
export const extractProcedures = (b) => resourcesOf(b, "Procedure");
export const extractEncounters = (b) => resourcesOf(b, "Encounter");
export const extractDiagnosticReports = (b) => resourcesOf(b, "DiagnosticReport");

// Distinct source organisations present in the bundle.
export const extractSources = (b) => [
  ...new Set((b?.entry || []).map((e) => e.resource?._source).filter(Boolean)),
];

// Blood group is carried as a Patient.extension (Norvic + Mediciti both emit it).
export function extractBloodGroup(patient) {
  const ext = (patient?.extension || []).find((e) =>
    e.url?.includes("patient-bloodGroup")
  );
  return ext?.valueString || null;
}

// Active (non-resolved) problems, newest onset first.
export function extractActiveConditions(b) {
  return resourcesOf(b, "Condition")
    .filter((c) => {
      const status =
        c.clinicalStatus?.coding?.[0]?.code || c.clinicalStatus?.text || "active";
      return status.toLowerCase() !== "resolved" && status.toLowerCase() !== "inactive";
    })
    .sort((a, z) => new Date(z.onsetDateTime || 0) - new Date(a.onsetDateTime || 0));
}

// All Observations split by FHIR category so vitals and labs never mix.
function categoryOf(o) {
  return o.category?.[0]?.coding?.[0]?.code || "";
}
export const extractVitalObservations = (b) =>
  resourcesOf(b, "Observation").filter((o) => categoryOf(o) === "vital-signs");
export const extractLabObservations = (b) =>
  resourcesOf(b, "Observation").filter((o) => categoryOf(o) === "laboratory");

// Most-recent single reading for a vital, matched by display name (case-insensitive).
export function latestVitalByName(b, name) {
  const wanted = name.toLowerCase();
  return extractVitalObservations(b)
    .filter((o) => (o.code?.text || "").toLowerCase().includes(wanted))
    .sort((a, z) => new Date(z.effectiveDateTime || 0) - new Date(a.effectiveDateTime || 0))[0] || null;
}

// Resolve a DiagnosticReport into its analyte Observations via result references.
// Falls back to `contained` for any source that ever embeds them.
export function groupLabReports(b) {
  const labObs = extractLabObservations(b);
  const byId = new Map(labObs.map((o) => [o.id, o]));
  return extractDiagnosticReports(b)
    .map((report) => {
      const refIds = (report.result || [])
        .map((r) => r.reference?.split("/").pop())
        .filter(Boolean);
      let analytes = refIds.map((id) => byId.get(id)).filter(Boolean);
      if (analytes.length === 0 && Array.isArray(report.contained)) {
        analytes = report.contained.filter((c) => c.resourceType === "Observation");
      }
      return { report, analytes };
    })
    .sort(
      (a, z) =>
        new Date(z.report.effectiveDateTime || 0) -
        new Date(a.report.effectiveDateTime || 0)
    );
}

// ---------------------------------------------------------------------------
// Reference-range classifier — shared source of truth for Normal/Borderline/High
// colour coding across Summary vitals tiles and the Latest Lab Results card.
// (Mirrors the ranges TrendsPanel uses for its charts.)
// ---------------------------------------------------------------------------
const REFERENCE_RANGES = {
  "systolic blood pressure": { normalMax: 120, high: 140 },
  "diastolic blood pressure": { normalMax: 80, high: 90 },
  "blood glucose": { normalMax: 100, high: 126 },
  glucose: { normalMax: 100, high: 126 },
  hba1c: { normalMax: 5.7, high: 6.5 },
  "ldl cholesterol": { normalMax: 100, high: 130 },
  "total cholesterol": { normalMax: 200, high: 240 },
  "heart rate": { normalMax: 100, high: 120 },
  "oxygen saturation": { low: 95, normalMax: 100, high: Infinity },
  hemoglobin: { normalMax: 17, high: 18 },
};

// Returns { label, tone } where tone is one of ok | warn | error | null.
export function classifyValue(name, value) {
  const v = typeof value === "number" ? value : parseFloat(value);
  if (Number.isNaN(v)) return { label: null, tone: null };
  const ref = REFERENCE_RANGES[(name || "").trim().toLowerCase()];
  if (!ref) return { label: null, tone: null };
  // SpO2-style ranges use a `low` floor (below it is the abnormal side).
  if (ref.low != null && v < ref.low) return { label: "Low", tone: "error" };
  if (ref.high != null && v >= ref.high && ref.high !== Infinity)
    return { label: "High", tone: "error" };
  if (ref.normalMax != null && v > ref.normalMax && ref.high !== Infinity)
    return { label: "Borderline", tone: "warn" };
  return { label: "Normal", tone: "ok" };
}
