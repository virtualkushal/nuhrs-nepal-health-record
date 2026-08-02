import { useEffect, useState } from "react";
import { UserPlus, Loader2, ShieldCheck, ShieldOff, Users, Clock, UserCheck, Check, X } from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import DashboardHeader from "../components/DashboardHeader";
import StatCard from "../components/StatCard";
import { ROLE_THEME, STAFF_ROLES, DEPARTMENTS } from "../constants";

const CREATE_ROLES = [...STAFF_ROLES, { value: "ADMIN", label: "Administrator" }];
const emptyForm = { email: "", full_name: "", role: "DOCTOR", department: "", password: "" };

// Admin dashboard: overview counts, pending staff approvals, staff directory,
// and manual staff creation.
export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("approvals");
  const [overview, setOverview] = useState(null);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  async function loadAll() {
    setLoading(true);
    try {
      const [ov, st] = await Promise.all([
        api.get("/v1/admin/overview/"),
        api.get("/v1/auth/staff/"),
      ]);
      setOverview(ov.data);
      setStaff(st.data.results || st.data);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { loadAll(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setFormError(""); setSaving(true);
    try {
      const payload = { ...form };
      if (payload.role !== "DOCTOR") delete payload.department;
      if (!payload.password) delete payload.password;
      await api.post("/v1/auth/staff/", payload);
      setForm(emptyForm);
      await loadAll();
    } catch (err) {
      const data = err.response?.data;
      setFormError(
        data && typeof data === "object"
          ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : v}`).join("  ")
          : "Could not create the account."
      );
    } finally { setSaving(false); }
  }

  async function approve(id) { await api.post(`/v1/auth/staff/${id}/approve/`); loadAll(); }
  async function reject(id) { await api.post(`/v1/auth/staff/${id}/reject/`); loadAll(); }
  async function toggleActive(m) { await api.patch(`/v1/auth/staff/${m.id}/`, { is_active: !m.is_active }); loadAll(); }

  const pending = staff.filter((m) => m.status === "PENDING");
  const deptLabel = (v) => DEPARTMENTS.find((d) => d.value === v)?.label || v || "—";

  return (
    <div className={`min-h-screen bg-gradient-to-b ${ROLE_THEME.ADMIN.tint}`}>
      <DashboardHeader user={user} logout={logout} subtitle="Staff & access control" />

      <div className="mx-auto max-w-6xl px-6 pt-6">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard icon={Users} label="Patients" value={overview?.patients ?? "…"} tone="slate" />
          <StatCard icon={UserCheck} label="Active staff" value={overview?.staff_active ?? "…"} tone="emerald" />
          <StatCard icon={Clock} label="Pending" value={overview?.staff_pending ?? "…"} tone="amber" />
          <StatCard icon={UserPlus} label="Open visits" value={overview?.encounters_open ?? "…"} tone="blue" />
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-6 pt-6">
        <div className="flex gap-2">
          {[["approvals", `Approvals${pending.length ? ` (${pending.length})` : ""}`], ["staff", "Staff"], ["add", "Add staff"]].map(([k, label]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${tab === k ? "bg-slate-800 text-white" : "bg-surface-750 text-gray-300 ring-1 ring-line"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <main className="mx-auto max-w-6xl px-6 py-6">
        {loading ? (
          <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-gray-500" /></div>
        ) : tab === "approvals" ? (
          <div className="rounded-2xl bg-surface-750 p-5 shadow-sm ring-1 ring-line">
            <h2 className="font-semibold text-white">Pending staff requests</h2>
            {pending.length === 0 ? (
              <p className="mt-3 text-sm text-gray-500">No pending requests.</p>
            ) : (
              <ul className="mt-3 divide-y divide-line">
                {pending.map((m) => (
                  <li key={m.id} className="flex items-center justify-between py-3">
                    <div>
                      <p className="font-medium text-white">{m.full_name}</p>
                      <p className="text-xs text-gray-400">{m.email} · {m.role} · {deptLabel(m.department)}</p>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => approve(m.id)} className="flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-emerald-700">
                        <Check className="h-4 w-4" /> Approve
                      </button>
                      <button onClick={() => reject(m.id)} className="flex items-center gap-1 rounded-lg bg-surface-700 px-3 py-1.5 text-sm font-semibold text-gray-200 hover:bg-surface-700">
                        <X className="h-4 w-4" /> Reject
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : tab === "staff" ? (
          <div className="overflow-hidden rounded-2xl bg-surface-750 shadow-sm ring-1 ring-line">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-gray-400">
                  <th className="px-6 py-3 font-medium">Name</th>
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">Role</th>
                  <th className="px-6 py-3 font-medium">Department</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 text-right font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {staff.map((m) => (
                  <tr key={m.id} className="border-b border-line">
                    <td className="px-6 py-3 text-white">{m.full_name}</td>
                    <td className="px-6 py-3 text-gray-300">{m.email}</td>
                    <td className="px-6 py-3"><span className="rounded-full bg-surface-700 px-2 py-0.5 text-xs text-gray-200">{m.role}</span></td>
                    <td className="px-6 py-3 text-gray-300">{deptLabel(m.department)}</td>
                    <td className="px-6 py-3">{m.is_active ? <span className="text-emerald-300">Active</span> : <span className="text-gray-500">{m.status}</span>}</td>
                    <td className="px-6 py-3 text-right">
                      {m.id === user?.id ? <span className="text-xs text-gray-500">You</span> : m.status !== "PENDING" && (
                        <button onClick={() => toggleActive(m)} className="inline-flex items-center gap-1 text-xs font-medium text-gray-300 hover:text-white">
                          {m.is_active ? <><ShieldOff className="h-4 w-4" /> Deactivate</> : <><ShieldCheck className="h-4 w-4" /> Activate</>}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="max-w-md rounded-2xl bg-surface-750 p-6 shadow-sm ring-1 ring-line">
            <h2 className="mb-4 flex items-center gap-2 font-semibold text-white"><UserPlus className="h-5 w-5 text-brand-300" /> Add staff</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <Field label="Full name" value={form.full_name} onChange={(v) => setForm({ ...form, full_name: v })} required />
              <Field label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} required />
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-200">Role</label>
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500">
                  {CREATE_ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              {form.role === "DOCTOR" && (
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-200">Department</label>
                  <select value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} required
                    className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500">
                    <option value="">Select…</option>
                    {DEPARTMENTS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
                  </select>
                </div>
              )}
              <Field label="Password (optional — emailed if blank)" type="password" value={form.password} onChange={(v) => setForm({ ...form, password: v })} />
              {formError && <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">{formError}</div>}
              <button type="submit" disabled={saving}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 font-medium text-white hover:bg-brand-500 disabled:opacity-60">
                {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <UserPlus className="h-5 w-5" />} Create account
              </button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", required }) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-200">{label}</label>
      <input type={type} value={value} required={required} onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500" />
    </div>
  );
}
