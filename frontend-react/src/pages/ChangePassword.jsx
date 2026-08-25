import { useState } from "react";
import { api } from "../lib/api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { FormBanner } from "../components/ui.jsx";
import { parseApiError } from "../lib/formErrors.js";
import { AuthLayout } from "./RegisterOrg.jsx";
import { PASSWORD_PATTERN, PASSWORD_TITLE } from "../lib/validation.js";

// Forced password change for accounts issued a temporary password.
export default function ChangePassword() {
  const { completePasswordChange } = useAuth();
  const { show } = useToast();
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setFormError("");
    try {
      await api.changePassword(pw);
      completePasswordChange();
      show("Password updated", "ok");
    } catch (err) {
      // This endpoint returns policy/verification failures as { detail }.
      setFormError(parseApiError(err).formError);
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
        <FormBanner message={formError} />
        <div>
          <label className="label" htmlFor="newpw">New password</label>
          <input
            id="newpw"
            type="password"
            className={`field ${formError ? "field-error" : ""}`}
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            pattern={PASSWORD_PATTERN}
            title={PASSWORD_TITLE}
            aria-invalid={formError ? "true" : undefined}
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
