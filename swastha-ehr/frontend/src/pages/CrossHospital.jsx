import { useEffect, useState } from "react";
import { Building2, Download, Loader2, RefreshCw, Send, ShieldCheck } from "lucide-react";
import api from "../services/api";
import DashboardHeader from "../components/DashboardHeader";
import { useAuth } from "../context/AuthContext";


// Doctor-facing cross-hospital exchange. This hospital's doctor asks a PEER
// hospital for a patient's records (by National ID + scope). The peer's patient
// or admin approves, then the bundle is fetched and can be imported into this DB.
const SCOPES = [
  { key: "diagnoses", label: "Diagnoses" },
  { key: "labs", label: "Lab results" },
  { key: "medications", label: "Medications" },
  { key: "everything", label: "Everything" },
];

export default function CrossHospital() {
  const { user, logout } = useAuth();
  const [peers, setPeers] = useState([]);

  const [self, setSelf] = useState(null);
  const [peerCode, setPeerCode] = useState("");
  const [nid, setNid] = useState("");
  const [scope, setScope] = useState(["everything"]);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function loadRegistry() {
    try {
      const res = await api.get("/v1/hospitals/");
      setSelf(res.data.self);
      setPeers(res.data.peers || []);
      if (res.data.peers?.[0]) setPeerCode(res.data.peers[0].code);
    } catch {
      setError("Could not load hospital registry.");
    }
  }

  async function loadRequests() {
    try {
      const res = await api.get("/v1/share/outbound/list/");
      setRequests(res.data.results || []);
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    loadRegistry();
    loadRequests();
  }, []);

  function toggleScope(key) {
    if (key === "everything") {
      setScope(["everything"]);
      return;
    }
    setScope((prev) => {
      const next = prev.filter((s) => s !== "everything");
      return next.includes(key) ? next.filter((s) => s !== key) : [...next, key];
    });
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.post("/v1/share/outbound/", {
        peer_code: peerCode,
        national_id: nid.trim(),
        scope,
      });
      setNid("");
      await loadRequests();
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not send the request.");
    } finally {
      setBusy(false);
    }
  }

  async function poll(id) {
    try {
      await api.post(`/v1/share/outbound/${id}/poll/`);
      await loadRequests();
    } catch {
      setError("Poll failed.");
    }
  }

  async function importRecord(id) {
    try {
      await api.post(`/v1/share/outbound/${id}/import/`);
      await loadRequests();
    } catch (err) {
      setError(err?.response?.data?.detail || "Import failed.");
    }
  }

  return (
    <div className="min-h-screen bg-surface-700">
      <DashboardHeader user={user} logout={logout} subtitle="Cross-Hospital Exchange" />

      <div className="mx-auto max-w-4xl px-4 py-8">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 p-2.5 shadow-sm">
            <Building2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Cross-Hospital Records Exchange</h1>
            <p className="text-sm text-gray-400">
              {self ? `${self.name} (${self.code})` : "This hospital"} — request a patient's records from another hospital via FHIR.
            </p>
          </div>
        </div>

        <form onSubmit={submit} className="rounded-2xl bg-surface-750 p-6 shadow-sm ring-1 ring-line">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-200">Hospital to request from</label>
              <select
                value={peerCode}
                onChange={(e) => setPeerCode(e.target.value)}
                className="w-full rounded-lg border border-line bg-surface-800 px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none"
              >
                {peers.length === 0 && <option value="">No peers configured</option>}
                {peers.map((p) => (
                  <option key={p.code} value={p.code}>
                    {p.name} ({p.code})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-200">Patient National ID</label>
              <input
                value={nid}
                onChange={(e) => setNid(e.target.value)}
                placeholder="e.g. 1234500001"
                required
                className="w-full rounded-lg border border-line bg-surface-800 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-brand-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="mb-2 block text-sm font-medium text-gray-200">Scope requested</label>
            <div className="flex flex-wrap gap-2">
              {SCOPES.map((s) => {
                const active = scope.includes(s.key);
                return (
                  <button
                    type="button"
                    key={s.key}
                    onClick={() => toggleScope(s.key)}
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      active ? "bg-brand-600 text-white" : "bg-surface-800 text-gray-300 ring-1 ring-line"
                    }`}
                  >
                    {s.label}
                  </button>
                );
              })}
            </div>
          </div>

          <button
            type="submit"
            disabled={busy || !peerCode}
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Send request
          </button>
          <p className="mt-2 flex items-center gap-1.5 text-xs text-gray-500">
            <ShieldCheck className="h-3.5 w-3.5" /> The other hospital's patient or admin must approve before records are shared.
          </p>
          {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
        </form>

        <div className="mt-6 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">My requests</h2>
          <button onClick={loadRequests} className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        </div>

        <div className="mt-3 space-y-3">
          {requests.length === 0 && (
            <p className="rounded-xl bg-surface-750 p-4 text-sm text-gray-500 ring-1 ring-line">No requests yet.</p>
          )}
          {requests.map((r) => (
            <div key={r.id} className="rounded-xl bg-surface-750 p-4 ring-1 ring-line">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white">
                    {r.peer_name} · NID {r.national_id}
                  </p>
                  <p className="text-xs text-gray-400">
                    Scope: {(r.scope || []).join(", ") || "everything"}
                  </p>
                </div>
                <StatusBadge status={r.status} imported={r.imported} />
              </div>

              {r.error && <p className="mt-2 text-xs text-red-300">{r.error}</p>}

              {r.status === "APPROVED" && r.summary && (
                <p className="mt-2 text-xs text-gray-400">
                  Received: {Object.entries(r.summary).map(([k, v]) => `${v} ${k}`).join(", ")}
                </p>
              )}

              <div className="mt-3 flex gap-2">
                {["PENDING", "ERROR"].includes(r.status) && (
                  <button
                    onClick={() => poll(r.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-surface-800 px-3 py-1.5 text-xs font-semibold text-white ring-1 ring-line hover:bg-surface-900"
                  >
                    <RefreshCw className="h-3.5 w-3.5" /> Check for approval
                  </button>
                )}
                {r.status === "APPROVED" && !r.imported && (
                  <button
                    onClick={() => importRecord(r.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700"
                  >
                    <Download className="h-3.5 w-3.5" /> Import into our records
                  </button>
                )}
                {r.imported && (
                  <span className="text-xs font-semibold text-emerald-300">Imported ✓</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status, imported }) {
  const map = {
    PENDING: "bg-amber-500/10 text-amber-300",
    APPROVED: "bg-emerald-500/10 text-emerald-300",
    DENIED: "bg-red-500/10 text-red-300",
    EXPIRED: "bg-gray-500/10 text-gray-300",
    ERROR: "bg-red-500/10 text-red-300",
  };
  const label = imported ? "IMPORTED" : status;
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${map[status] || "bg-gray-500/10 text-gray-300"}`}>
      {label}
    </span>
  );
}
