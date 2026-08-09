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
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4 rounded-2xl bg-surface-container-lowest p-8 shadow-sm ring-1 ring-outline-variant">
        <div className="flex flex-col items-center">
          <div className="rounded-2xl bg-primary p-3 shadow-sm">
            <KeyRound className="h-6 w-6 text-white" />
          </div>
          <h1 className="mt-3 text-xl font-bold text-on-surface">Set a new password</h1>
          {user?.must_change_password && (
            <p className="mt-1 text-center text-sm text-warn">
              For security, please change your temporary password before continuing.
            </p>
          )}
        </div>
        {error && (
          <div className="rounded-lg bg-error/10 px-4 py-3 text-sm text-error ring-1 ring-error/30">{error}</div>
        )}
        {["Current password", "New password", "Confirm new password"].map((label, i) => (
          <div key={label}>
            <label className="mb-1 block text-sm font-medium text-on-surface">{label}</label>
            <input
              type="password"
              required
              minLength={i === 0 ? undefined : 8}
              value={[oldPassword, newPassword, confirm][i]}
              onChange={(e) => [setOld, setNew, setConfirm][i](e.target.value)}
              className="w-full rounded-lg border border-outline-variant bg-surface-container-lowest text-on-surface placeholder-on-surface-variant/60 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        ))}
        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          Update password
        </button>
      </form>
    </div>
  );
}
