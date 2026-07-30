import { useEffect, useState } from "react";
import { Archive, ChevronDown, ChevronUp, FlaskConical, Pill, Stethoscope, User } from "lucide-react";
import api from "../services/api";
import DashboardHeader from "../components/DashboardHeader";
import { useAuth } from "../context/AuthContext";

export default function ImportedRecords() {
  const { user, logout } = useAuth();
  const [records, setRecords] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [detail, setDetail] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/v1/share/external-records/")
      .then((r) => setRecords(r.data.results || []))
      .finally(() => setLoading(false));
  }, []);

  async function toggle(id) {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    if (!detail[id]) {
      const r = await api.get(`/v1/share/external-records/${id}/`);
      setDetail((d) => ({ ...d, [id]: r.data.sections }));
    }
  }

  return (
    <div className="min-h-screen bg-surface-700">
      <DashboardHeader user={user} logout={logout} subtitle="Imported Records" />
      <div className="mx-auto max-w-4xl px-4 py-8">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 p-2.5 shadow-sm">
            <Archive className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Imported Records</h1>
            <p className="text-sm text-gray-400">Patient data received from other hospitals via FHIR.</p>
          </div>
        </div>

        {loading && <p className="text-sm text-gray-400">Loading…</p>}
        {!loading && records.length === 0 && (
          <p className="rounded-xl bg-surface-750 p-4 text-sm text-gray-500 ring-1 ring-line">
            No imported records yet. Use Cross-Hospital Exchange to request and import records.
          </p>
        )}

        <div className="space-y-3">
          {records.map((r) => (
            <div key={r.id} className="rounded-xl bg-surface-750 ring-1 ring-line">
              <button
                onClick={() => toggle(r.id)}
                className="flex w-full items-center justify-between px-4 py-3 text-left"
              >
                <div>
                  <p className="text-sm font-semibold text-white">
                    NID {r.national_id} — from {r.source_hospital_name} ({r.source_hospital_code})
                  </p>
                  <p className="text-xs text-gray-400">
                    Scope: {(r.scope || []).join(", ") || "everything"} ·{" "}
                    {Object.entries(r.summary || {}).map(([k, v]) => `${v} ${k}`).join(", ")} ·{" "}
                    {new Date(r.created_at).toLocaleDateString()}
                  </p>
                </div>
                {expanded === r.id
                  ? <ChevronUp className="h-4 w-4 text-gray-400" />
                  : <ChevronDown className="h-4 w-4 text-gray-400" />}
              </button>

              {expanded === r.id && detail[r.id] && (
                <div className="border-t border-line px-4 pb-4 pt-3 space-y-4">
                  <PatientCard p={detail[r.id].patient} />
                  <Section icon={<Stethoscope className="h-4 w-4" />} title="Diagnoses" rows={detail[r.id].diagnoses}
                    cols={["display", "code", "status", "date"]} />
                  <Section icon={<FlaskConical className="h-4 w-4" />} title="Lab Results" rows={detail[r.id].labs}
                    cols={["display", "value", "unit", "date"]} />
                  <Section icon={<Pill className="h-4 w-4" />} title="Medications" rows={detail[r.id].medications}
                    cols={["medication", "dosage", "status", "date"]} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PatientCard({ p }) {
  if (!p) return null;
  return (
    <div className="flex items-center gap-3 rounded-lg bg-surface-800 px-3 py-2">
      <User className="h-5 w-5 text-brand-400" />
      <div className="text-sm text-white">
        <span className="font-semibold">{p.name}</span>
        <span className="ml-3 text-gray-400">{p.gender} · DOB {p.birthDate} · {p.phone}</span>
      </div>
    </div>
  );
}

function Section({ icon, title, rows, cols }) {
  if (!rows || rows.length === 0) return null;
  return (
    <div>
      <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
        {icon} {title}
      </p>
      <div className="overflow-x-auto rounded-lg ring-1 ring-line">
        <table className="w-full text-xs text-gray-300">
          <thead className="bg-surface-800 text-gray-500">
            <tr>{cols.map((c) => <th key={c} className="px-3 py-2 text-left capitalize">{c}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-t border-line hover:bg-surface-800/50">
                {cols.map((c) => <td key={c} className="px-3 py-2">{row[c] ?? "—"}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
