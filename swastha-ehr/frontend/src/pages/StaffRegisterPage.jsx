import { useState } from "react";
import { Link } from "react-router-dom";
import { HeartPulse, Loader2, CheckCircle2 } from "lucide-react";
import api from "../services/api";
import { STAFF_ROLES, DEPARTMENTS } from "../constants";

// Public staff self-registration -> creates a PENDING account for admin approval.
export default function StaffRegisterPage() {
  const [form, setForm] = useState({ email: "", full_name: "", role: "RECEPTIONIST", department: "" });
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = { ...form };
      if (payload.role !== "DOCTOR") delete payload.department;
      await api.post("/v1/auth/register/", payload);
      setDone(true);
    } catch (err) {
      const data = err?.response?.data;
      setError(data?.email?.[0] || data?.role?.[0] || data?.department?.[0] || data?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-surface-900 to-surface-800 px-4">
        <div className="w-full max-w-md rounded-2xl bg-surface-750 p-8 text-center shadow-lg ring-1 ring-line">
          <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500" />
          <h1 className="mt-4 text-xl font-bold text-white">Request received</h1>
          <p className="mt-2 text-sm text-gray-300">
            An administrator will review and approve your account. Once approved, you'll get an email with a temporary password.
          </p>
          <Link to="/login" className="mt-6 inline-block rounded-lg bg-brand-600 px-5 py-2.5 font-semibold text-white hover:bg-brand-500">
            Back to sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-surface-900 to-surface-800 px-4 py-10">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4 rounded-2xl bg-surface-750 p-8 shadow-lg ring-1 ring-line">
        <div className="flex flex-col items-center">
          <div className="rounded-2xl bg-gradient-to-br from-teal-500 to-blue-600 p-3 shadow-md">
            <HeartPulse className="h-6 w-6 text-white" />
          </div>
          <h1 className="mt-3 text-xl font-bold text-white">Staff account request</h1>
          <p className="text-sm text-gray-400">Approved by an administrator before access</p>
        </div>
        {error && <div className="rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-300 ring-1 ring-red-500/30">{error}</div>}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-200">Full name</label>
          <input required value={form.full_name} onChange={(e) => update("full_name", e.target.value)}
            className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-200">Email</label>
          <input type="email" required value={form.email} onChange={(e) => update("email", e.target.value)}
            className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-200">Role</label>
          <select value={form.role} onChange={(e) => update("role", e.target.value)}
            className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
            {STAFF_ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
        {form.role === "DOCTOR" && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-200">Department</label>
            <select required value={form.department} onChange={(e) => update("department", e.target.value)}
              className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
              <option value="">Select a department…</option>
              {DEPARTMENTS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
            </select>
          </div>
        )}
        <button type="submit" disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 font-semibold text-white shadow-sm transition hover:bg-brand-500 disabled:opacity-60">
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          Submit request
        </button>
        <p className="text-center text-sm text-gray-400">
          <Link to="/login" className="text-brand-400 hover:underline">Back to sign in</Link>
        </p>
      </form>
    </div>
  );
}
