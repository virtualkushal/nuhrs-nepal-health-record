import { extractImmunizations } from "../../lib/fhirUtils.js";
import { fmtDate } from "./util.js";

// Vaccination history in a simple card list — vaccine, dose/lot, date, source.

export default function ImmunizationsFriendly({ bundle }) {
  const imms = [...extractImmunizations(bundle)].sort(
    (a, z) => new Date(z.occurrenceDateTime || 0) - new Date(a.occurrenceDateTime || 0)
  );

  if (imms.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-8 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] opacity-40">vaccines</span>
        <p className="mt-2 text-body-md">No vaccination records yet.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {imms.map((im, i) => {
        const dose = im.protocolApplied?.[0]?.doseNumberString || im.protocolApplied?.[0]?.doseNumberPositiveInt;
        const meta = [dose ? `Dose ${dose}` : null, im.lotNumber ? `Lot ${im.lotNumber}` : null]
          .filter(Boolean)
          .join(" · ");
        return (
          <div
            key={i}
            className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-5 flex gap-3"
          >
            <span className="material-symbols-outlined text-primary mt-0.5">vaccines</span>
            <div className="min-w-0 flex-1">
              <div className="font-title-lg text-title-lg text-on-surface">
                {im.vaccineCode?.text || "Vaccine"}
              </div>
              {meta && <div className="text-label-sm text-on-surface-variant">{meta}</div>}
              <div className="text-label-sm text-on-surface-variant mt-1">
                {fmtDate(im.occurrenceDateTime)}
                {im._source ? ` · ${im._source}` : ""}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
