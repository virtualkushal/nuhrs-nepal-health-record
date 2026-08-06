import { useEffect, useState } from "react";
import { api } from "../../lib/api.js";
import { fmtDate } from "./util.js";

// National Health Updates — the Ministry-authored announcements feed, read via
// the public authenticated list endpoint. Category-tinted cards from the mock.

const CATEGORY = {
  VACCINATION_DRIVE: { label: "Vaccination Drive", icon: "vaccines", cls: "bg-ok/10 text-ok" },
  SYSTEM_UPDATE: { label: "System Update", icon: "campaign", cls: "bg-secondary/10 text-secondary" },
  PUBLIC_HEALTH: { label: "Public Health", icon: "health_and_safety", cls: "bg-primary/10 text-primary" },
  GENERAL: { label: "General", icon: "info", cls: "bg-surface-container-highest text-on-surface-variant" },
};

export default function AnnouncementsFeed() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listAnnouncements().then(setItems).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-body-md text-error">{error}</p>;
  if (!items) return <p className="text-body-md text-on-surface-variant">Loading updates…</p>;
  if (items.length === 0) {
    return <p className="text-body-md text-on-surface-variant">No health updates right now.</p>;
  }

  return (
    <div className="space-y-4">
      {items.map((a) => {
        const c = CATEGORY[a.category] || CATEGORY.GENERAL;
        return (
          <article
            key={a.id}
            className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-6"
          >
            <div className="flex items-center justify-between gap-3 mb-2">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-label-sm text-label-sm ${c.cls}`}>
                <span className="material-symbols-outlined text-[16px]">{c.icon}</span>
                {c.label}
              </span>
              <span className="text-label-sm text-on-surface-variant whitespace-nowrap">
                {fmtDate(a.published_at)}
              </span>
            </div>
            <h3 className="font-headline-md text-headline-md text-on-surface">{a.title}</h3>
            <p className="text-body-md text-on-surface-variant mt-2 whitespace-pre-line">{a.body}</p>
            {a.author_name && (
              <div className="text-label-sm text-on-surface-variant mt-3">
                — {a.author_name}, Ministry of Health
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}
