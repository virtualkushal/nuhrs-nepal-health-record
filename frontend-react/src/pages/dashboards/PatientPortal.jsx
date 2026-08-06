import { useEffect, useState } from "react";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card, Table, Badge } from "../../components/ui.jsx";
import UserChangePassword from "../../components/UserChangePassword.jsx";

// Patient's own read-only record view.
export default function PatientPortal() {
  const { show } = useToast();
  const [data, setData] = useState(null);
  const [tab, setTab] = useState("records");

  useEffect(() => {
    api.myRecords().then(setData).catch((e) => show(e.message, "err"));
  }, []);

  if (!data)
    return <Card title="My Health Record"><p className="text-on-surface-variant">Loading your records…</p></Card>;

  const p = data.patient;
  return (
    <div className="space-y-stack-lg">
      <div className="flex gap-2 border-b border-outline-variant">
        {[
          { id: "records", label: "My Records" },
          { id: "settings", label: "Account Settings" },
        ].map((t) => (
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

      {tab === "records" && (
        <Card title="My Health Record">
          <h3 className="font-headline-lg text-[22px]">
            {p.full_name} <span className="text-on-surface-variant text-body-md">{p.nid}</span>
          </h3>
          <p className="text-on-surface-variant mb-4">
            DOB {p.date_of_birth} · {p.gender}
          </p>
          <Table head={["Type", "Summary", "Facility", "Date"]}>
            {data.records.length === 0 && (
              <tr><td colSpan={4} className="py-3 text-on-surface-variant">No records yet</td></tr>
            )}
            {data.records.map((r, i) => (
              <tr key={i} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{r.resource_type}</td>
                <td className="py-2 pr-4">{r.summary}</td>
                <td className="py-2 pr-4"><Badge>{r.organization_name}</Badge></td>
                <td className="py-2 pr-4">{r.service_date}</td>
              </tr>
            ))}
          </Table>
        </Card>
      )}

      {tab === "settings" && (
        <Card title="Account Settings">
          <UserChangePassword />
        </Card>
      )}
    </div>
  );
}
