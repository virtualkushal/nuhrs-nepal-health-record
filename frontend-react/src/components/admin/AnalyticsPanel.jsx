import { useEffect, useState } from "react";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card, Table } from "../ui.jsx";

// National health analytics, aggregated from record metadata (no clinical
// data). Shared verbatim by the Super Admin and Ministry dashboards — the
// backend gates `analytics/summary/` to those two roles only.
export default function AnalyticsPanel() {
  const { show } = useToast();
  const [a, setA] = useState(null);
  useEffect(() => {
    api.analytics().then(setA).catch((e) => show(e.message, "err"));
  }, []);

  if (!a) return <Card title="National Health Analytics"><p className="text-on-surface-variant">Loading analytics…</p></Card>;

  const stat = (n, l) => (
    <div className="p-stack-lg bg-surface-container-low rounded-xl text-center">
      <div className="font-display-lg text-[32px] text-primary tabular-nums">{n}</div>
      <div className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">{l}</div>
    </div>
  );

  return (
    <div className="space-y-stack-lg">
      <Card title="National Health Analytics" subtitle="Aggregated from record metadata — a public-health benefit of unified records.">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stat(a.total_patients, "Patients")}
          {stat(a.total_records_indexed, "Records Indexed")}
          {stat(a.total_organizations, "Active Orgs")}
          {stat(a.total_exchanges, "Exchanges")}
        </div>
      </Card>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
        <Card title="Top Diagnoses">
          <Table head={["Condition", "Count"]}>
            {(a.top_conditions || []).map((c, i) => (
              <tr key={i} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{c.summary}</td>
                <td className="py-2 pr-4">{c.count}</td>
              </tr>
            ))}
            {(!a.top_conditions || a.top_conditions.length === 0) && (
              <tr><td colSpan={2} className="py-3 text-on-surface-variant">No data</td></tr>
            )}
          </Table>
        </Card>
        <Card title="Records by Province">
          <Table head={["Province", "Count"]}>
            {(a.records_by_province || []).map((p, i) => (
              <tr key={i} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{p["organization__province"] || "Unknown"}</td>
                <td className="py-2 pr-4">{p.count}</td>
              </tr>
            ))}
            {(!a.records_by_province || a.records_by_province.length === 0) && (
              <tr><td colSpan={2} className="py-3 text-on-surface-variant">No data</td></tr>
            )}
          </Table>
        </Card>
      </div>
    </div>
  );
}
