// Blue "Patient Summary" tile from the Stitch "Grouped Clinical Records" design.
// All figures are derived from the real index data (no hardcoded values).
export default function PatientSummaryCard({ index = [], allergies = 0 }) {
  // Distinct service dates give us the history span and a proxy for "visits".
  const dates = index
    .map((r) => r.service_date)
    .filter(Boolean)
    .map((d) => new Date(d))
    .filter((d) => !Number.isNaN(d.getTime()))
    .sort((a, b) => a - b);

  let spanLabel = "—";
  if (dates.length >= 1) {
    const first = dates[0];
    const last = dates[dates.length - 1];
    const years = Math.max(0, last.getFullYear() - first.getFullYear());
    if (years >= 1) {
      spanLabel = `${years} Year${years > 1 ? "s" : ""}`;
    } else {
      const months = Math.max(
        1,
        (last.getFullYear() - first.getFullYear()) * 12 +
          (last.getMonth() - first.getMonth())
      );
      spanLabel = `${months} Month${months > 1 ? "s" : ""}`;
    }
  }

  const encounters = index.filter((r) => r.resource_type === "Encounter").length;
  const visits = encounters || index.length;

  return (
    <div className="bg-primary text-on-primary rounded-lg p-6 shadow-lg relative overflow-hidden">
      <div className="relative z-10">
        <span className="font-label-sm text-label-sm uppercase opacity-80">
          Patient Summary
        </span>
        <div className="mt-4 space-y-4">
          <div>
            <div className="font-headline-lg text-[32px] leading-none">
              {spanLabel}
            </div>
            <div className="font-label-sm text-label-sm">Medical History Span</div>
          </div>
          <div className="flex gap-6 border-t border-on-primary/20 pt-4">
            <div>
              <div className="font-headline-md text-headline-md">
                {String(visits).padStart(2, "0")}
              </div>
              <div className="font-label-sm text-label-sm">Records</div>
            </div>
            <div>
              <div className="font-headline-md text-headline-md">
                {String(allergies).padStart(2, "0")}
              </div>
              <div className="font-label-sm text-label-sm">Allergies</div>
            </div>
          </div>
        </div>
      </div>
      <div className="absolute -right-8 -bottom-8 opacity-10 scale-150 pointer-events-none">
        <span className="material-symbols-outlined text-[120px]">history_edu</span>
      </div>
    </div>
  );
}
