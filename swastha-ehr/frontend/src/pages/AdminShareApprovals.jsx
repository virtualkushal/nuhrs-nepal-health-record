import { useEffect, useState } from "react";
import { Check, Inbox, RefreshCw, X } from "lucide-react";
import api from "../services/api";
import DashboardHeader from "../components/DashboardHeader";
import { useAuth } from "../context/AuthContext";


// Admin view of INBOUND cross-hospital requests: other hospitals asking for our
// patients' records. Admin can approve or deny (the patient can also approve in
// their own portal — whichever happens first).
export default function AdminShareApprovals() {
  const { user, logout } = useAuth();
  const [rows, setRows] = useState([]);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await api.get("/v1/admin/share-requests/");
      setRows(res.data.results || []);
    } catch {
      setError("Could not load share requests.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function decide(id, decision) {
    setError("");
    try {
      await api.post(`/v1/admin/share-requests/${id}/decision/`, { decision });
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Action failed.");
    }
  }

  return (
    <div className="min-h-screen bg-surface-700">
      <DashboardHeader user={user} logout={logout} subtitle="Incoming Requests" />

      <div className="mx-auto max-w-4xl px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 p-2.5 shadow-sm">
              <Inbox className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Incoming Record Requests</h1>
              <p className="text-sm text-gray-400">Other hospitals requesting our patients' records.</p>
            </div>
          </div>
          <button onClick={load} className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </button>
        </div>

        {error && <p className="mb-3 text-sm text-red-300">{error}</p>}
        {loading && <p className="text-sm text-gray-500">Loading…</p>}

        <div className="space-y-3">
          {rows.length === 0 && !loading && (
            <p className="rounded-xl bg-surface-750 p-4 text-sm text-gray-500 ring-1 ring-line">No requests.</p>
          )}
          {rows.map((r) => (
            <div key={r.id} className="rounded-xl bg-surface-750 p-4 ring-1 ring-line">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white">
                    {r.requester_label || r.requester_hospital || "External hospital"} · NID {r.national_id}
                  </p>
                  <p className="text-xs text-gray-400">
                    Scope: {(r.scope || []).join(", ") || "everything"}
                    {!r.patient_known && " · ⚠ no local patient with this NID"}
                  </p>
                </div>
                <span className="rounded-full bg-surface-700 px-2.5 py-0.5 text-xs font-semibold text-gray-300">
                  {r.status}
                </span>
              </div>

              {r.status === "PENDING" && (
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => decide(r.id, "APPROVE")}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700"
                  >
                    <Check className="h-3.5 w-3.5" /> Approve
                  </button>
                  <button
                    onClick={() => decide(r.id, "DENY")}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700"
                  >
                    <X className="h-3.5 w-3.5" /> Deny
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
