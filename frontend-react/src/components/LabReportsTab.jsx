import { useState } from "react";
import { groupLabReports, classifyValue } from "../lib/fhirUtils.js";

// All DiagnosticReports as a 2-col card grid. Each card shows the panel name,
// LOINC chip, date, source, and an expandable analyte table resolved from the
// report's result[] references (laboratory Observations).

function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

const TONE_TEXT = { ok: "text-ok", warn: "text-warn", error: "text-error" };

function AnalyteRow({ o }) {
  const v = o.valueQuantity?.value ?? o.valueString;
  const unit = o.valueQuantity?.unit || "";
  const range = o.referenceRange?.[0]?.text;
  const flag = o.interpretation?.[0]?.coding?.[0]?.code || o.interpretation?.[0]?.text;
  const { tone } = classifyValue(o.code?.text, o.valueQuantity?.value);
  return (
    <div className="grid grid-cols-12 gap-3 px-4 py-3 bg-surface-container-low rounded-lg items-center border border-outline-variant/20">
      <div className="col-span-6">
        <div className="font-label-md text-label-md text-on-surface">{o.code?.text || "Analyte"}</div>
        {range && <div className="text-[11px] text-on-surface-variant">Ref: {range}</div>}
      </div>
      <div className="col-span-4 text-center">
        <span className={`font-title-lg text-title-lg tabular-nums ${tone ? TONE_TEXT[tone] : "text-on-surface"}`}>
          {v ?? "—"}
        </span>{" "}
        <span className="text-label-sm text-on-surface-variant">{unit}</span>
      </div>
      <div className="col-span-2 text-right">
        {flag && (
          <span className={`text-[10px] font-bold uppercase ${tone === "error" ? "text-error" : "text-primary"}`}>
            {flag}
          </span>
        )}
      </div>
    </div>
  );
}

function ReportCard({ group }) {
  const [open, setOpen] = useState(true);
  const { report, analytes } = group;
  const loinc = report.code?.coding?.[0]?.code;
  return (
    <div className="bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 p-6 flex flex-col">
      <button onClick={() => setOpen((v) => !v)} className="flex items-start justify-between gap-3 text-left">
        <div>
          <div className="flex items-center gap-2 text-primary mb-1">
            <span className="material-symbols-outlined text-[18px]">science</span>
            <span className="font-label-sm text-label-sm uppercase tracking-widest font-bold">Laboratory Panel</span>
          </div>
          <h3 className="font-headline-md text-headline-md text-on-surface">
            {report.code?.text || "Laboratory Panel"}
          </h3>
        </div>
        <div className="text-right shrink-0">
          <div className="font-label-md text-label-md text-on-surface">{fmtDate(report.effectiveDateTime)}</div>
          {loinc && (
            <span className="inline-block mt-1 px-3 py-0.5 bg-primary/10 text-primary font-label-sm text-label-sm rounded-full">
              LOINC: {loinc}
            </span>
          )}
        </div>
      </button>

      {open && (
        <div className="space-y-2 mt-4">
          {analytes.length === 0 ? (
            <p className="text-body-md text-on-surface-variant">
              {report.conclusion || "No individual analytes reported."}
            </p>
          ) : (
            analytes.map((o, i) => <AnalyteRow key={i} o={o} />)
          )}
        </div>
      )}

      {report._source && (
        <div className="mt-4 pt-3 border-t border-outline-variant/30 flex items-center gap-1 text-on-surface-variant">
          <span className="material-symbols-outlined text-[14px]">biotech</span>
          <span className="font-label-sm text-label-sm uppercase tracking-widest">Source: {report._source}</span>
        </div>
      )}
    </div>
  );
}

export default function LabReportsTab({ bundle }) {
  const groups = groupLabReports(bundle);

  if (groups.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 p-8 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] opacity-40">science</span>
        <p className="mt-2 text-body-md">No lab reports available.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
      {groups.map((g, i) => (
        <ReportCard key={i} group={g} />
      ))}
    </div>
  );
}
