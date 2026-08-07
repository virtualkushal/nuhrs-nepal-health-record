import { extractEncounters } from "../../lib/fhirUtils.js";
import { fmtDate } from "./util.js";

// Plain-language list of the patient's clinical visits — reason, hospital,
// date, and (when present) the doctor. No FHIR codes or provenance emphasis.

export default function RecentVisits({ bundle, limit }) {
  const visits = [...extractEncounters(bundle)].sort(
    (a, z) => new Date(z.period?.start || 0) - new Date(a.period?.start || 0)
  );
  const shown = limit ? visits.slice(0, limit) : visits;

  if (shown.length === 0) {
    return <p className="text-body-md text-on-surface-variant">No visits on record yet.</p>;
  }

  return (
    <ul className="space-y-3">
      {shown.map((e, i) => {
        const doctor = e.participant?.[0]?.individual?.display;
        return (
          <li key={i} className="flex items-start gap-3 p-4 bg-surface-container-low rounded-xl">
            <span className="material-symbols-outlined text-primary mt-0.5">local_hospital</span>
            <div className="min-w-0 flex-1">
              <div className="font-label-md text-label-md text-on-surface">
                {e.reasonCode?.[0]?.text || e.type?.[0]?.text || "Clinical visit"}
              </div>
              <div className="text-label-sm text-on-surface-variant">
                {e.serviceProvider?.display || e._source || "—"}
                {doctor ? ` · ${doctor}` : ""}
              </div>
            </div>
            <span className="text-label-sm text-on-surface-variant whitespace-nowrap">
              {fmtDate(e.period?.start)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
