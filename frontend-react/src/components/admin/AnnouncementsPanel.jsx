import { useEffect, useState } from "react";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card, Table, Badge, Field } from "../ui.jsx";

const CATEGORY_OPTIONS = [
  { value: "PUBLIC_HEALTH", label: "Public Health" },
  { value: "VACCINATION_DRIVE", label: "Vaccination Drive" },
  { value: "SYSTEM_UPDATE", label: "System Update" },
  { value: "GENERAL", label: "General" },
];

const CATEGORY_LABELS = Object.fromEntries(
  CATEGORY_OPTIONS.map((c) => [c.value, c.label])
);

// Compose + list + delete national announcements. Shared verbatim by the Super
// Admin and Ministry dashboards — broadcasting is a power both roles hold, so
// the one implementation lives here rather than being duplicated per dashboard.
export default function AnnouncementsPanel() {
  const { show } = useToast();
  const [items, setItems] = useState(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState("PUBLIC_HEALTH");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      setItems(await api.listAnnouncements());
    } catch (e) {
      show(e.message, "err");
    }
  };
  useEffect(() => {
    load();
  }, []);

  async function create(e) {
    e.preventDefault();
    if (!title.trim() || !body.trim()) {
      show("Title and body are required", "err");
      return;
    }
    setBusy(true);
    try {
      await api.createAnnouncement({ title, body, category });
      show("Announcement published", "ok");
      setTitle("");
      setBody("");
      setCategory("PUBLIC_HEALTH");
      load();
    } catch (e) {
      show(e.message, "err");
    } finally {
      setBusy(false);
    }
  }

  async function remove(id) {
    try {
      await api.deleteAnnouncement(id);
      show("Announcement deleted");
      load();
    } catch (e) {
      show(e.message, "err");
    }
  }

  return (
    <div className="space-y-stack-lg">
      <Card title="Publish Announcement" subtitle="Health updates and news shown to every patient in their portal.">
        <form onSubmit={create} className="space-y-4 max-w-2xl">
          <Field label="Title" id="ann-title" value={title} onChange={setTitle} placeholder="e.g. Free measles-rubella vaccination camp" />
          <div>
            <label className="label" htmlFor="ann-body">Message</label>
            <textarea
              id="ann-body"
              className="field min-h-[120px]"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Write the announcement patients will read…"
            />
          </div>
          <div>
            <label className="label" htmlFor="ann-category">Category</label>
            <select
              id="ann-category"
              className="field max-w-xs"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {CATEGORY_OPTIONS.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="px-6 py-3 bg-primary text-on-primary rounded-lg disabled:opacity-50"
          >
            {busy ? "Publishing…" : "Publish Announcement"}
          </button>
        </form>
      </Card>

      <Card title="Published Announcements">
        {!items ? (
          <p className="text-on-surface-variant">Loading announcements…</p>
        ) : (
          <Table head={["Title", "Category", "Published", "Author", "Action"]}>
            {items.length === 0 && (
              <tr><td colSpan={5} className="py-3 text-on-surface-variant">No announcements yet</td></tr>
            )}
            {items.map((a) => (
              <tr key={a.id} className="border-b border-outline-variant/60">
                <td className="py-3 pr-4">
                  {a.title}
                  <div className="text-label-sm text-on-surface-variant line-clamp-1">{a.body}</div>
                </td>
                <td className="py-3 pr-4">
                  <Badge>{CATEGORY_LABELS[a.category] || a.category}</Badge>
                </td>
                <td className="py-3 pr-4 tabular-nums">
                  {new Date(a.published_at).toLocaleDateString()}
                </td>
                <td className="py-3 pr-4">{a.author_name || "—"}</td>
                <td className="py-3 pr-4">
                  <button
                    onClick={() => remove(a.id)}
                    className="px-3 py-1.5 rounded-lg bg-error/10 text-error font-label-md text-label-sm"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
}
