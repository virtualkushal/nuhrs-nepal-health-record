import { useState } from "react";
import { useToast } from "../context/ToastContext.jsx";
import { api } from "../lib/api.js";
import { FieldError, FormBanner } from "./ui.jsx";
import { parseApiError } from "../lib/formErrors.js";

// Self-service password change. Verifies the current password server-side
// before applying the new one (see ChangePasswordView).
export default function UserChangePassword() {
  const { show } = useToast();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setErrors({});
    setFormError("");
    // Client-side checks, reported inline on the offending field.
    const nextErrors = {};
    if (newPassword !== confirmPassword) {
      nextErrors.confirm = "New passwords do not match.";
    }
    if (newPassword.length < 6) {
      nextErrors.new = "Password must be at least 6 characters.";
    }
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      return;
    }
    setBusy(true);
    try {
      await api.changePassword(newPassword, currentPassword);
      show("Password updated successfully", "ok");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      // The endpoint reports "Current password is incorrect" / policy failures
      // as { detail } — surface it in the banner.
      setFormError(parseApiError(err).formError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-md">
      <h2 className="font-title-lg text-title-lg mb-4">Change Password</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormBanner message={formError} />
        <div>
          <label className="label" htmlFor="cur-pw">Current Password</label>
          <input
            id="cur-pw"
            type="password"
            className="field"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label" htmlFor="new-pw">New Password</label>
          <input
            id="new-pw"
            type="password"
            className={`field ${errors.new ? "field-error" : ""}`}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            aria-invalid={errors.new ? "true" : undefined}
            aria-describedby={errors.new ? "new-pw-error" : undefined}
            required
          />
          <FieldError id="new-pw-error">{errors.new}</FieldError>
        </div>
        <div>
          <label className="label" htmlFor="confirm-pw">Confirm New Password</label>
          <input
            id="confirm-pw"
            type="password"
            className={`field ${errors.confirm ? "field-error" : ""}`}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            aria-invalid={errors.confirm ? "true" : undefined}
            aria-describedby={errors.confirm ? "confirm-pw-error" : undefined}
            required
          />
          <FieldError id="confirm-pw-error">{errors.confirm}</FieldError>
        </div>
        <button
          type="submit"
          disabled={busy}
          className="px-6 py-3 bg-primary text-on-primary rounded-lg disabled:opacity-50"
        >
          {busy ? "Updating…" : "Update Password"}
        </button>
      </form>
    </div>
  );
}
