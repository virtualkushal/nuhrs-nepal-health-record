// All Conditions (active + resolved) as a card list with a left-border accent:
// red for active problems, gray for resolved.

function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function statusOf(c) {
  return (c.clinicalStatus?.coding?.[0]?.code || c.clinicalStatus?.text || "active").toLowerCase();
}

export default function ConditionsTab({ bundle }) {
  const conditions = (bundle?.entry || [])
    .map((e) => e.resource)
    .filter((r) => r?.resourceType === "Condition")
    .sort((a, z) => new Date(z.onsetDateTime || 0) - new Date(a.onsetDateTime || 0));

  if (conditions.length === 0) {
    return (
      <div className="bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 p-8 text-center text-on-surface-variant">
        <span className="material-symbols-outlined text-[40px] opacity-40">coronavirus</span>
        <p className="mt-2 text-body-md">No conditions on record.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {conditions.map((c, i) => {
        const active = statusOf(c) !== "resolved" && statusOf(c) !== "inactive";
        const icd = c.code?.coding?.[0]?.code;
        return (
          <div
            key={i}
            className={`bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 border-l-4 p-5 ${
              active ? "border-l-error" : "border-l-outline-variant"
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <h3 className="font-title-lg text-title-lg text-on-surface">{c.code?.text || "Condition"}</h3>
              <span className={`px-2.5 py-0.5 rounded-full font-label-sm text-label-sm capitalize ${
                active ? "bg-error/10 text-error" : "bg-surface-variant text-on-surface-variant"
              }`}>
                {statusOf(c)}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {icd && (
                <span className="text-[11px] bg-surface-container-highest text-on-surface-variant px-2 py-0.5 rounded-full">
                  ICD-10: {icd}
                </span>
              )}
              <span className="font-label-sm text-label-sm text-on-surface-variant">
                Onset {fmtDate(c.onsetDateTime)}
              </span>
            </div>
            {c._source && (
              <div className="mt-3 pt-3 border-t border-outline-variant/30 flex items-center gap-1 text-on-surface-variant">
                <span className="material-symbols-outlined text-[14px]">domain</span>
                <span className="font-label-sm text-label-sm uppercase tracking-widest">Source: {c._source}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
