import {
  extractEncounters,
  groupLabReports,
  extractMedications,
  extractImmunizations,
  extractVitalObservations,
} from "../../lib/fhirUtils.js";
import { fmtDate } from "./util.js";

// The clean, chrome-free document used for "Save as PDF". It lives off-canvas
// (see `.print-doc` in index.css) and is revealed only in the browser's print
// dialog, so the exported PDF is just the record — no app shell. Deliberately
// uses plain black-on-white styling (not theme colors) so it prints crisply
// even when browsers drop background colours.

function latestVitals(bundle) {
  const byName = new Map();
  for (const o of extractVitalObservations(bundle)) {
    const name = o.code?.text || "Vital";
    const prev = byName.get(name);
    if (!prev || new Date(o.effectiveDateTime || 0) > new Date(prev.effectiveDateTime || 0)) {
      byName.set(name, o);
    }
  }
  return [...byName.entries()].map(([name, o]) => ({
    name,
    value: o.valueQuantity?.value,
    unit: o.valueQuantity?.unit || "",
    date: o.effectiveDateTime,
  }));
}

function Section({ title, children }) {
  return (
    <section className="mt-6">
      <h2 className="text-[15px] font-semibold text-gray-900 border-b border-gray-400 pb-1 mb-2 uppercase tracking-wide">
        {title}
      </h2>
      {children}
    </section>
  );
}

function Empty({ text }) {
  return <p className="text-[12px] text-gray-500 italic">{text}</p>;
}

export default function PrintableRecord({ patient, bloodGroup, bundle }) {
  const vitals = latestVitals(bundle);
  const labs = groupLabReports(bundle);
  const meds = extractMedications(bundle);
  const imms = [...extractImmunizations(bundle)].sort(
    (a, z) => new Date(z.occurrenceDateTime || 0) - new Date(a.occurrenceDateTime || 0)
  );
  const visits = [...extractEncounters(bundle)].sort(
    (a, z) => new Date(z.period?.start || 0) - new Date(a.period?.start || 0)
  );
  const generated = new Date().toLocaleString();

  return (
    <div className="print-doc bg-white text-gray-900" style={{ fontFamily: "Inter, sans-serif" }}>
      <div className="p-2">
        {/* Header */}
        <div className="flex items-start justify-between border-b-2 border-gray-800 pb-3">
          <div>
            <div className="text-[18px] font-bold">NUHRS — National Health Record</div>
            <div className="text-[12px] text-gray-600">Nepal Unified Health Record System · Ministry of Health</div>
          </div>
          <div className="text-[11px] text-gray-600 text-right">
            Generated<br />
            {generated}
          </div>
        </div>

        {/* Identity */}
        <div className="grid grid-cols-2 gap-x-8 gap-y-1 mt-4 text-[13px]">
          <div><span className="text-gray-500">Name: </span><span className="font-semibold">{patient?.full_name || "—"}</span></div>
          <div><span className="text-gray-500">National ID: </span><span className="font-semibold">{patient?.nid || "—"}</span></div>
          <div><span className="text-gray-500">Date of Birth: </span>{fmtDate(patient?.date_of_birth)}</div>
          <div><span className="text-gray-500">Gender: </span>{patient?.gender ? patient.gender.charAt(0) + patient.gender.slice(1).toLowerCase() : "—"}</div>
          <div><span className="text-gray-500">Blood Group: </span><span className="font-semibold">{bloodGroup || "—"}</span></div>
        </div>

        {/* Vitals */}
        <Section title="Latest Vitals">
          {vitals.length === 0 ? (
            <Empty text="No vitals recorded." />
          ) : (
            <table className="w-full text-[12px] border-collapse">
              <tbody>
                {vitals.map((v, i) => (
                  <tr key={i} className="border-b border-gray-200">
                    <td className="py-1 pr-4">{v.name}</td>
                    <td className="py-1 pr-4 font-semibold tabular-nums">
                      {v.value ?? "—"} {v.unit}
                    </td>
                    <td className="py-1 text-gray-500 text-right">{fmtDate(v.date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>

        {/* Lab Results */}
        <Section title="Lab Results">
          {labs.length === 0 ? (
            <Empty text="No lab results recorded." />
          ) : (
            labs.map((g, i) => (
              <div key={i} className="mb-3">
                <div className="text-[13px] font-semibold">
                  {g.report.code?.text || "Lab Panel"}
                  <span className="text-gray-500 font-normal"> · {fmtDate(g.report.effectiveDateTime)}</span>
                </div>
                {g.analytes.length === 0 ? (
                  <div className="text-[12px] text-gray-600">{g.report.conclusion || "No detailed results."}</div>
                ) : (
                  <table className="w-full text-[12px] border-collapse">
                    <tbody>
                      {g.analytes.map((o, j) => (
                        <tr key={j} className="border-b border-gray-200">
                          <td className="py-1 pr-4">{o.code?.text || "Result"}</td>
                          <td className="py-1 font-semibold tabular-nums text-right">
                            {o.valueQuantity?.value ?? o.valueString ?? "—"} {o.valueQuantity?.unit || ""}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ))
          )}
        </Section>

        {/* Medications */}
        <Section title="Medications">
          {meds.length === 0 ? (
            <Empty text="No medications recorded." />
          ) : (
            <table className="w-full text-[12px] border-collapse">
              <tbody>
                {meds.map((m, i) => (
                  <tr key={i} className="border-b border-gray-200">
                    <td className="py-1 pr-4 font-semibold">{m.medicationCodeableConcept?.text || "Medication"}</td>
                    <td className="py-1 pr-4">{m.dosageInstruction?.[0]?.text || "As directed"}</td>
                    <td className="py-1 text-gray-500 text-right">{fmtDate(m.authoredOn)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>

        {/* Immunizations */}
        <Section title="Immunizations">
          {imms.length === 0 ? (
            <Empty text="No vaccinations recorded." />
          ) : (
            <table className="w-full text-[12px] border-collapse">
              <tbody>
                {imms.map((im, i) => (
                  <tr key={i} className="border-b border-gray-200">
                    <td className="py-1 pr-4 font-semibold">{im.vaccineCode?.text || "Vaccine"}</td>
                    <td className="py-1 pr-4">{im.lotNumber ? `Lot ${im.lotNumber}` : ""}</td>
                    <td className="py-1 text-gray-500 text-right">{fmtDate(im.occurrenceDateTime)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>

        {/* Visits */}
        <Section title="Clinical Visits">
          {visits.length === 0 ? (
            <Empty text="No visits recorded." />
          ) : (
            <table className="w-full text-[12px] border-collapse">
              <tbody>
                {visits.map((e, i) => (
                  <tr key={i} className="border-b border-gray-200">
                    <td className="py-1 pr-4">{e.reasonCode?.[0]?.text || e.type?.[0]?.text || "Clinical visit"}</td>
                    <td className="py-1 pr-4 text-gray-600">{e.serviceProvider?.display || e._source || "—"}</td>
                    <td className="py-1 text-gray-500 text-right">{fmtDate(e.period?.start)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>

        <p className="mt-8 pt-3 border-t border-gray-300 text-[10px] text-gray-500">
          This document was generated from the patient's own aggregated National Health Record.
          Values are informational and should be interpreted together with a qualified clinician.
        </p>
      </div>
    </div>
  );
}
