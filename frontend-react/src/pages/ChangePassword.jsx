import { useState } from "react";
import { api } from "../lib/api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { AuthLayout } from "./RegisterOrg.jsx";
import { PASSWORD_PATTERN, PASSWORD_TITLE } from "../lib/validation.js";

// Forced password change for accounts issued a temporary password.
export default function ChangePassword() {
  const { completePasswordChange } = useAuth();
  const { show } = useToast();
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.changePassword(pw);
      completePasswordChange();
      show("Password updated", "ok");
    } catch (err) {
      show(err.message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Set a new password"
      subtitle="Your account uses a temporary password. Please change it."
    >
      <form className="space-y-5" onSubmit={submit}>
        <div>
          <label className="label">New password</label>
          <input
            type="password"
            className="field"
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            pattern={PASSWORD_PATTERN}
            title={PASSWORD_TITLE}
            required
          />
          <p className="mt-1 text-xs text-muted">{PASSWORD_TITLE}</p>
        </div>
        <button type="submit" disabled={busy} className="btn-primary w-full">
          {busy ? "Updating…" : "Update password"}
        </button>
      </form>
    </AuthLayout>
  );
}
