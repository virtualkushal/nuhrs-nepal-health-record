import { Badge } from "./ui.jsx";

// Renders a single FHIR resource returned by the unified fetch.
// Mirrors the logic of the original renderResource() helper.
export default function ResourceCard({ resource: r }) {
  const type = r.resourceType;
  const src = r._source ? <Badge>{r._source}</Badge> : null;

  if (type === "Patient") return null; // identity shown in header

  if (type === "OperationOutcome") {
    return (
      <div className="border-l-4 border-warn bg-warn/5 rounded-r-lg px-4 py-3 mb-3">
        <h4 className="font-title-lg text-title-lg flex items-center gap-2">
          Source unavailable {src}
        </h4>
        <div className="text-body-md text-on-surface-variant mt-1">
          {r.issue?.[0]?.diagnostics || ""}
        </div>
      </div>
    );
  }

  let title = type;
  let detail = null;

  if (type === "Condition") {
    title = "Diagnosis: " + (r.code?.text || "—");
    detail = `ICD: ${r.code?.coding?.[0]?.code || "—"} · onset ${r.onsetDateTime || "—"}`;
  } else if (type === "Observation") {
    title = r.code?.text || "Observation";
    detail = `${r.valueQuantity?.value ?? ""} ${r.valueQuantity?.unit ?? ""} · ${r.effectiveDateTime || ""}`;
  } else if (type === "DiagnosticReport") {
    title = "Lab Report: " + (r.code?.text || "—");
    detail = (
      <>
        {(r.effectiveDateTime || "") + " · " + (r.conclusion || "")}
        <ul className="list-disc ml-5 mt-2 space-y-1">
          {(r.contained || []).map((o, i) => (
            <li key={i}>
              {o.code?.text}: {o.valueQuantity?.value} {o.valueQuantity?.unit}{" "}
              <span className="text-on-surface-variant">
                ({o.referenceRange?.[0]?.text || ""})
              </span>
            </li>
          ))}
        </ul>
      </>
    );
  } else if (type === "Encounter") {
    title = "Encounter: " + (r.reasonCode?.[0]?.text || r.class?.code || "—");
    detail = `${r.period?.start || ""} · ${r.participant?.[0]?.individual?.display || ""}`;
  }

  return (
    <div className="border-l-4 border-primary bg-surface-container-low rounded-r-lg px-4 py-3 mb-3">
      <h4 className="font-title-lg text-title-lg flex items-center gap-2">
        {title} {src}
      </h4>
      {detail && (
        <div className="text-body-md text-on-surface-variant mt-1">{detail}</div>
      )}
    </div>
  );
}
