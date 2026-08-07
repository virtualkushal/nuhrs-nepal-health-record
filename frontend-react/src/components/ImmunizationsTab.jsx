import { extractImmunizations } from "../lib/fhirUtils.js";

// All Immunizations (Norvic emits these; Mediciti does not). Shows an
// explicit empty state for Mediciti-only patients rather than a blank tab.

function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export default function ImmunizationsTab({ bundle }) {
  const imms = extractImmunizations(bundle).sort(
    (a, z) => new Date(z.occurrenceDateTime || 0) - new Date(a.occurrenceDateTime || 0)
  );

  if (imms.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 p-8 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] opacity-40">vaccines</span>
        <p className="mt-2 text-body-md">No immunization records available.</p>
      </div>
    );
  }

  return (
    <div className="bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-surface-container-low border-b border-surface-container">
            <tr>
              {["Vaccine", "Date", "Dose", "Source"].map((h) => (
                <th key={h} className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-container">
            {imms.map((im, i) => (
              <tr key={i} className="hover:bg-surface-container-low transition-colors">
                <td className="px-6 py-4 font-label-md text-label-md text-on-surface">
                  {im.vaccineCode?.text || "Vaccine"}
                </td>
                <td className="px-6 py-4 font-body-md text-body-md text-on-surface-variant tabular-nums">
                  {fmtDate(im.occurrenceDateTime)}
                </td>
                <td className="px-6 py-4 font-body-md text-body-md text-on-surface-variant">
                  {im.protocolApplied?.[0]?.doseNumberString || "—"}
                </td>
                <td className="px-6 py-4 font-label-sm text-label-sm text-on-surface-variant">
                  {im._source || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
