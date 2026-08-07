import { extractMedications } from "../../lib/fhirUtils.js";
import { fmtDate } from "./util.js";

// Simple medication cards — drug, dose instruction, prescriber, date.
// A plainer take on the doctor's MedicationsTab, without provenance emphasis.

export default function MyMedications({ bundle }) {
  const meds = extractMedications(bundle);

  if (meds.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-8 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] opacity-40">medication</span>
        <p className="mt-2 text-body-md">No medications on record.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {meds.map((m, i) => (
        <div
          key={i}
          className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-5 flex gap-3"
        >
          <span className="material-symbols-outlined text-primary mt-0.5">medication</span>
          <div className="min-w-0">
            <div className="font-title-lg text-title-lg text-on-surface">
              {m.medicationCodeableConcept?.text || "Medication"}
            </div>
            <div className="text-body-md text-on-surface-variant">
              {m.dosageInstruction?.[0]?.text || "As directed"}
            </div>
            <div className="text-label-sm text-on-surface-variant mt-1">
              {m.requester?.display ? `Prescribed by ${m.requester.display}` : "Prescriber —"}
              {" · "}
              {fmtDate(m.authoredOn)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
