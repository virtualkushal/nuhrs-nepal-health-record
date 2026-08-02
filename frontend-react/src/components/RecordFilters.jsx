// Left "Timeline Filters" rail from the Stitch design.
// Record-type chips + source-hospital checkboxes, both driven by real index data.

const TYPE_CHIPS = [
  { key: "ALL", label: "All" },
  { key: "Encounter", label: "Encounters" },
  { key: "Observation", label: "Vitals" },
  { key: "DiagnosticReport", label: "Labs" },
  { key: "Condition", label: "Conditions" },
];

export default function RecordFilters({
  index = [],
  activeType,
  onTypeChange,
  sources = [],
  activeSources,
  onToggleSource,
}) {
  // Count records per source hospital from the real index.
  const sourceCounts = {};
  for (const r of index) {
    const name = r.organization_name || "Unknown source";
    sourceCounts[name] = (sourceCounts[name] || 0) + 1;
  }

  return (
    <div className="bg-surface-container-lowest rounded-lg p-6 shadow-sm border border-outline-variant/30">
      <div className="flex items-center gap-2 mb-6">
        <span className="material-symbols-outlined text-primary">filter_list</span>
        <h3 className="font-headline-md text-headline-md text-on-surface">
          Timeline Filters
        </h3>
      </div>

      <div className="space-y-8">
        <section>
          <label className="font-label-sm text-label-sm text-on-surface-variant uppercase mb-4 block tracking-wider">
            Record Types
          </label>
          <div className="flex flex-wrap gap-2">
            {TYPE_CHIPS.map((chip) => {
              const active = activeType === chip.key;
              return (
                <button
                  key={chip.key}
                  onClick={() => onTypeChange(chip.key)}
                  className={`px-4 py-2 rounded font-label-md text-label-md flex items-center gap-1 transition-colors ${
                    active
                      ? "bg-primary text-on-primary"
                      : "bg-surface-container text-on-surface-variant hover:bg-surface-variant"
                  }`}
                >
                  {active && (
                    <span className="material-symbols-outlined text-[18px]">
                      check
                    </span>
                  )}
                  {chip.label}
                </button>
              );
            })}
          </div>
        </section>

        <section>
          <label className="font-label-sm text-label-sm text-on-surface-variant uppercase mb-4 block tracking-wider">
            Source Hospitals
          </label>
          <div className="space-y-2">
            {sources.length === 0 && (
              <p className="text-body-md text-on-surface-variant">
                No sources yet.
              </p>
            )}
            {sources.map((name) => {
              const checked = activeSources.includes(name);
              return (
                <label
                  key={name}
                  className={`flex items-center gap-4 p-2 hover:bg-surface-container rounded cursor-pointer transition-colors ${
                    checked ? "" : "opacity-50"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => onToggleSource(name)}
                    className="w-4 h-4 rounded border-outline-variant text-primary focus:ring-primary accent-primary"
                  />
                  <span className="font-body-md text-body-md text-on-surface">
                    {name}
                  </span>
                  <span className="ml-auto font-label-sm text-label-sm bg-surface-variant px-1.5 rounded text-on-surface-variant">
                    {sourceCounts[name] || 0}
                  </span>
                </label>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
