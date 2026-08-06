// Horizontal underline-style tab bar for the doctor dashboard.
// Scrolls horizontally on narrow screens. Mirrors the tab pattern already used
// in SuperAdmin / PatientPortal / OrgAdmin.

const TABS = [
  { key: "summary", label: "Clinical Summary", icon: "summarize" },
  { key: "vitals", label: "Vitals & Trends", icon: "monitoring" },
  { key: "labs", label: "Lab Reports", icon: "science" },
  { key: "medications", label: "Medications", icon: "medication" },
  { key: "conditions", label: "Conditions", icon: "coronavirus" },
  { key: "encounters", label: "Encounters", icon: "medical_information" },
  { key: "immunizations", label: "Immunizations", icon: "vaccines" },
];

export default function TabBar({ activeTab, onTabChange, labReportCount = 0, tabs = TABS }) {
  return (
    <div className="border-b border-outline-variant/40 overflow-x-auto">
      <nav className="flex gap-1 min-w-max">
        {tabs.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 font-label-md text-label-md uppercase tracking-wider whitespace-nowrap transition-colors ${
                active
                  ? "border-primary text-primary"
                  : "border-transparent text-on-surface-variant hover:text-on-surface hover:border-outline-variant"
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">
                {tab.icon}
              </span>
              {tab.label}
              {tab.key === "labs" && labReportCount > 0 && (
                <span className="ml-1 bg-primary/10 text-primary text-label-sm font-label-sm px-1.5 rounded-full">
                  {labReportCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
