import {
  extractEncounters,
  groupLabReports,
  extractMedications,
  extractImmunizations,
} from "../../lib/fhirUtils.js";

// A compact "care at a glance" strip — honest counts of what's actually in the
// bundle (visits, lab panels, medications, vaccinations). Purely derived data,
// no fabricated status widgets.

const ITEMS = [
  { key: "visits", label: "Visits", icon: "local_hospital", count: (b) => extractEncounters(b).length },
  { key: "labs", label: "Lab Panels", icon: "science", count: (b) => groupLabReports(b).length },
  { key: "meds", label: "Medications", icon: "medication", count: (b) => extractMedications(b).length },
  { key: "imm", label: "Vaccinations", icon: "vaccines", count: (b) => extractImmunizations(b).length },
];

export default function CareSummary({ bundle }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {ITEMS.map((it) => (
        <div
          key={it.key}
          className="bg-surface-container-lowest rounded-2xl shadow-sm border border-outline-variant/30 p-5 flex items-center gap-4"
        >
          <span className="w-11 h-11 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-[22px]">{it.icon}</span>
          </span>
          <div>
            <div className="font-headline-lg text-[28px] leading-none text-on-surface tabular-nums">
              {it.count(bundle)}
            </div>
            <div className="text-label-sm text-on-surface-variant mt-1">{it.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
