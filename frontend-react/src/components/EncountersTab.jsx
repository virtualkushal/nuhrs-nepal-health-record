import { extractEncounters } from "../lib/fhirUtils.js";

// All Encounters as a scoped vertical timeline — the old cross-type timeline
// now lives here, focused on visits only. Encounters carry no free-text notes
// in the source data, so we surface reason / practitioner / facility instead.

function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export default function EncountersTab({ bundle }) {
  const encounters = extractEncounters(bundle).sort(
    (a, z) => new Date(z.period?.start || 0) - new Date(a.period?.start || 0)
  );

  if (encounters.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 p-8 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] opacity-40">medical_information</span>
        <p className="mt-2 text-body-md">No encounters on record.</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="absolute left-8 top-0 bottom-0 w-px bg-outline-variant/30" />
      <div className="flex flex-col gap-6">
        {encounters.map((e, i) => (
          <div key={i} className="relative pl-20 group">
            <div className="absolute left-[30px] top-6 w-4 h-4 rounded-full border-4 border-surface bg-primary shadow-sm z-10 group-hover:scale-125 transition-transform" />
            <div className="bg-surface-container-lowest rounded-lg shadow-md border-l-4 border-primary border border-outline-variant/30 p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="font-headline-md text-headline-md text-on-surface">
                  {e.reasonCode?.[0]?.text || e.type?.[0]?.text || "Clinical Visit"}
                </h2>
                <span className="font-label-md text-label-md text-on-surface">{fmtDate(e.period?.start)}</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-surface-container-low p-4 rounded-lg">
                <div>
                  <div className="font-label-sm text-label-sm text-on-surface-variant">Practitioner</div>
                  <div className="font-title-lg text-title-lg text-on-surface">
                    {e.participant?.[0]?.individual?.display || "—"}
                  </div>
                </div>
                <div className="sm:border-l border-outline-variant sm:pl-4">
                  <div className="font-label-sm text-label-sm text-on-surface-variant">Facility</div>
                  <div className="font-title-lg text-title-lg text-on-surface">
                    {e.serviceProvider?.display || e._source || "—"}
                  </div>
                </div>
              </div>
              {e._source && (
                <div className="mt-4 pt-3 border-t border-outline-variant/30 flex items-center gap-1 text-on-surface-variant">
                  <span className="material-symbols-outlined text-[14px]">verified</span>
                  <span className="font-label-sm text-label-sm uppercase tracking-widest">Source: {e._source}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
