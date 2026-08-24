import { useState } from "react";
import AnnouncementsPanel from "../../components/admin/AnnouncementsPanel.jsx";
import AnalyticsPanel from "../../components/admin/AnalyticsPanel.jsx";

// Ministry-of-Health dashboard: a deliberately restricted view with exactly two
// powers — broadcasting national announcements and reading national analytics.
// It reuses the very panels the Super Admin dashboard shows, but exposes nothing
// else (no provider registry, user management, ministry accounts, or audit log).
const TABS = [
  { id: "announcements", label: "Announcements" },
  { id: "analytics", label: "National Analytics" },
];

export default function Ministry() {
  const [tab, setTab] = useState("announcements");
  return (
    <div className="space-y-stack-lg">
      <div className="flex gap-2 border-b border-outline-variant">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-3 font-label-md border-b-2 -mb-px transition-colors ${
              tab === t.id
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-primary"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "announcements" && <AnnouncementsPanel />}
      {tab === "analytics" && <AnalyticsPanel />}
    </div>
  );
}
