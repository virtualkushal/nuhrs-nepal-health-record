import { useState } from "react";
import { useToast } from "../context/ToastContext.jsx";
import { api } from "../lib/api.js";

// Self-service password change. Verifies the current password server-side
// before applying the new one (see ChangePasswordView).
export default function UserChangePassword() {
  const { show } = useToast();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      show("New passwords do not match", "err");
      return;
    }
    if (newPassword.length < 6) {
      show("Password must be at least 6 characters", "err");
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
      show(err.message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-md">
      <h2 className="font-title-lg text-title-lg mb-4">Change Password</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Current Password</label>
          <input
            type="password"
            className="field"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">New Password</label>
          <input
            type="password"
            className="field"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">Confirm New Password</label>
          <input
            type="password"
            className="field"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
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
