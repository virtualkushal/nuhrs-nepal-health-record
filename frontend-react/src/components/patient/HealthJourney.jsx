import { extractImmunizations, extractEncounters, groupLabReports } from "../../lib/fhirUtils.js";
import { fmtDate } from "./util.js";

// The mock's vertical timeline: visits, lab reports, and vaccinations merged
// into one friendly reverse-chronological feed so the patient sees their care
// story in one place.

function buildEvents(bundle) {
  const events = [];

  for (const e of extractEncounters(bundle)) {
    events.push({
      date: e.period?.start,
      icon: "local_hospital",
      title: e.reasonCode?.[0]?.text || e.type?.[0]?.text || "Clinical visit",
      detail: e.serviceProvider?.display || e._source || "",
    });
  }
  for (const g of groupLabReports(bundle)) {
    events.push({
      date: g.report.effectiveDateTime,
      icon: "science",
      title: g.report.code?.text || "Lab test",
      detail: g.report._source || "",
    });
  }
  for (const im of extractImmunizations(bundle)) {
    events.push({
      date: im.occurrenceDateTime,
      icon: "vaccines",
      title: im.vaccineCode?.text || "Vaccination",
      detail: im._source || "",
    });
  }

  return events
    .filter((ev) => ev.date)
    .sort((a, z) => new Date(z.date) - new Date(a.date));
}

export default function HealthJourney({ bundle, limit }) {
  const events = buildEvents(bundle);
  const shown = limit ? events.slice(0, limit) : events;

  if (shown.length === 0) {
    return (
      <p className="text-body-md text-on-surface-variant">
        Your health journey will appear here as you receive care.
      </p>
    );
  }

  return (
    <ol className="relative border-l-2 border-outline-variant/50 ml-3 space-y-6">
      {shown.map((ev, i) => (
        <li key={i} className="ml-6">
          <span className="absolute -left-[15px] flex items-center justify-center w-7 h-7 rounded-full bg-primary/10 text-primary">
            <span className="material-symbols-outlined text-[16px]">{ev.icon}</span>
          </span>
          <div className="flex items-baseline justify-between gap-3">
            <span className="font-label-md text-label-md text-on-surface">{ev.title}</span>
            <span className="text-label-sm text-on-surface-variant whitespace-nowrap">
              {fmtDate(ev.date)}
            </span>
          </div>
          {ev.detail && (
            <div className="text-label-sm text-on-surface-variant">{ev.detail}</div>
          )}
        </li>
      ))}
    </ol>
  );
}
