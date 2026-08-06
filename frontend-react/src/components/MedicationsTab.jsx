import { extractMedications } from "../lib/fhirUtils.js";

// All MedicationRequests as a table (desktop) / cards (mobile).
// The source systems store no medication status (no completed/discontinued
// field exists), so we deliberately show none — only fields backed by data:
// drug, dosage, prescriber, prescribed date, and originating facility.

function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export default function MedicationsTab({ bundle }) {
  const meds = extractMedications(bundle);

  if (meds.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 p-8 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] opacity-40">medication</span>
        <p className="mt-2 text-body-md">No medications on record.</p>
      </div>
    );
  }

  return (
    <div className="bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-surface-container-low border-b border-surface-container">
            <tr>
              {["Medication", "Dosage", "Prescriber", "Prescribed", "Source"].map((h) => (
                <th key={h} className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-container">
            {meds.map((m, i) => (
              <tr key={i} className="hover:bg-surface-container-low transition-colors">
                <td className="px-6 py-4 font-label-md text-label-md text-on-surface">
                  {m.medicationCodeableConcept?.text || "Medication"}
                </td>
                <td className="px-6 py-4 font-body-md text-body-md text-on-surface-variant">
                  {m.dosageInstruction?.[0]?.text || "—"}
                </td>
                <td className="px-6 py-4 font-body-md text-body-md text-on-surface-variant">
                  {m.requester?.display || "—"}
                </td>
                <td className="px-6 py-4 font-body-md text-body-md text-on-surface-variant tabular-nums">
                  {fmtDate(m.authoredOn)}
                </td>
                <td className="px-6 py-4 font-label-sm text-label-sm text-on-surface-variant">
                  {m._source || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
