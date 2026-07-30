import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { KeyRound, Loader2 } from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import { ROLE_HOME } from "../constants";

// Forced/voluntary password change for a signed-in user.
export default function ChangePasswordPage() {
  const [oldPassword, setOld] = useState("");
  const [newPassword, setNew] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { user, clearMustChangePassword } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (newPassword !== confirm) {
      setError("New passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/v1/auth/change-password/", {
        old_password: oldPassword,
        new_password: newPassword,
      });
      clearMustChangePassword();
      navigate(ROLE_HOME[user.role] || "/", { replace: true });
    } catch (err) {
      const data = err?.response?.data;
      setError(data?.old_password?.[0] || data?.new_password?.[0] || data?.detail || "Could not change password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-surface-900 to-surface-800 px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4 rounded-2xl bg-surface-750 p-8 shadow-lg ring-1 ring-line">
        <div className="flex flex-col items-center">
          <div className="rounded-2xl bg-gradient-to-br from-teal-500 to-blue-600 p-3 shadow-md">
            <KeyRound className="h-6 w-6 text-white" />
          </div>
          <h1 className="mt-3 text-xl font-bold text-white">Set a new password</h1>
          {user?.must_change_password && (
            <p className="mt-1 text-center text-sm text-amber-300">
              For security, please change your temporary password before continuing.
            </p>
          )}
        </div>
        {error && (
          <div className="rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-300 ring-1 ring-red-500/30">{error}</div>
        )}
        {["Current password", "New password", "Confirm new password"].map((label, i) => (
          <div key={label}>
            <label className="mb-1 block text-sm font-medium text-gray-200">{label}</label>
            <input
              type="password"
              required
              minLength={i === 0 ? undefined : 8}
              value={[oldPassword, newPassword, confirm][i]}
              onChange={(e) => [setOld, setNew, setConfirm][i](e.target.value)}
              className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
        ))}
        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 font-semibold text-white shadow-sm transition hover:bg-brand-500 disabled:opacity-60"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          Update password
        </button>
      </form>
    </div>
  );
}
