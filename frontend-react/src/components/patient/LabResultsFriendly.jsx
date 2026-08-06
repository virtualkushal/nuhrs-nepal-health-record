import { useState } from "react";
import { groupLabReports, classifyValue } from "../../lib/fhirUtils.js";
import { fmtDate, friendlyLabel, TONE_DOT, TONE_SOFT } from "./util.js";

// Full numeric lab values (the user chose full detail) presented plainly:
// panel name, each analyte with value + unit + a soft Normal/Watch/High chip,
// and an informational note. LOINC codes and reference ranges are hidden behind
// an optional expander — never front-and-centre.

function Analyte({ o, showRange }) {
  const value = o.valueQuantity?.value ?? o.valueString;
  const unit = o.valueQuantity?.unit || "";
  const range = o.referenceRange?.[0]?.text;
  const { label: cls, tone } = classifyValue(o.code?.text, o.valueQuantity?.value);
  const friendly = friendlyLabel(cls);

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-3 bg-surface-container-low rounded-lg">
      <div className="min-w-0">
        <div className="font-label-md text-label-md text-on-surface">
          {o.code?.text || "Result"}
        </div>
        {showRange && range && (
          <div className="text-[11px] text-on-surface-variant">Typical range: {range}</div>
        )}
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <span className="font-title-lg text-title-lg text-on-surface tabular-nums">
          {value ?? "—"}
        </span>
        {unit && <span className="text-label-sm text-on-surface-variant">{unit}</span>}
        {friendly && (
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-label-sm text-label-sm ${
              tone ? TONE_SOFT[tone] : "bg-surface-container-highest text-on-surface-variant"
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${tone ? TONE_DOT[tone] : "bg-outline"}`} />
            {friendly}
          </span>
        )}
      </div>
    </div>
  );
}

function Panel({ group }) {
  const [showRange, setShowRange] = useState(false);
  const { report, analytes } = group;

  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-6">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="min-w-0">
          <h3 className="font-headline-md text-headline-md text-on-surface">
            {report.code?.text || "Lab Panel"}
          </h3>
          {report._source && (
            <div className="text-label-sm text-on-surface-variant">{report._source}</div>
          )}
        </div>
        <span className="font-label-md text-label-md text-on-surface-variant whitespace-nowrap">
          {fmtDate(report.effectiveDateTime)}
        </span>
      </div>

      {analytes.length === 0 ? (
        <p className="text-body-md text-on-surface-variant">
          {report.conclusion || "No detailed results reported."}
        </p>
      ) : (
        <>
          <div className="space-y-2">
            {analytes.map((o, i) => (
              <Analyte key={i} o={o} showRange={showRange} />
            ))}
          </div>
          <button
            onClick={() => setShowRange((v) => !v)}
            className="mt-3 text-primary font-label-sm text-label-sm hover:underline"
          >
            {showRange ? "Hide typical ranges" : "Show typical ranges"}
          </button>
        </>
      )}
    </div>
  );
}

export default function LabResultsFriendly({ bundle }) {
  const groups = groupLabReports(bundle);

  if (groups.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-8 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] opacity-40">science</span>
        <p className="mt-2 text-body-md">No lab results yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 p-4 rounded-xl bg-secondary-fixed text-on-secondary-fixed">
        <span className="material-symbols-outlined text-[20px]">info</span>
        <p className="text-body-md">
          These results are for your information. A colored label is only a guide —
          please discuss what they mean with your doctor.
        </p>
      </div>
      {groups.map((g, i) => (
        <Panel key={i} group={g} />
      ))}
    </div>
  );
}
