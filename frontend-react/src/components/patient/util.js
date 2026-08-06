// Small shared helpers for the patient-friendly portal components.
// These keep presentation calm and lay-person readable; all clinical parsing
// still lives in ../../lib/fhirUtils.js.

export function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime())
    ? d
    : dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

// Soften the clinician label from classifyValue() for a lay audience.
// "Borderline" reads as alarming out of context → "Watch". Normal/High/Low pass through.
export function friendlyLabel(label) {
  if (!label) return null;
  if (label === "Borderline") return "Watch";
  return label;
}

export const TONE_DOT = { ok: "bg-ok", warn: "bg-warn", error: "bg-error" };
export const TONE_TEXT = { ok: "text-ok", warn: "text-warn", error: "text-error" };
export const TONE_SOFT = {
  ok: "bg-ok/10 text-ok",
  warn: "bg-warn/10 text-warn",
  error: "bg-error/10 text-error",
};
