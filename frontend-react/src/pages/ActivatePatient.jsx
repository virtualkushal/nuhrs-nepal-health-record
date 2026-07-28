import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api.js";
import { useToast } from "../context/ToastContext.jsx";
import { Field } from "../components/ui.jsx";
import { AuthLayout } from "./RegisterOrg.jsx";

// Public patient self-activation form.
export default function ActivatePatient() {
  const navigate = useNavigate();
  const { show } = useToast();
  const [f, setF] = useState({ nid: "", date_of_birth: "", phone: "", password: "" });
  const [busy, setBusy] = useState(false);
  const set = (k) => (v) => setF((s) => ({ ...s, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.activatePatient(f);
      show("Account activated — you can now sign in", "ok");
      navigate("/");
    } catch (err) {
      show(err.message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Activate Patient Account"
      subtitle="Verify your identity to access your own records."
    >
      <form className="space-y-5" onSubmit={submit}>
        <Field label="National ID (NID)" id="nid" value={f.nid} onChange={set("nid")} placeholder="NID-1001" />
        <Field label="Date of birth" id="dob" type="date" value={f.date_of_birth} onChange={set("date_of_birth")} />
        <Field label="Phone" id="phone" value={f.phone} onChange={set("phone")} placeholder="9841000001" />
        <Field label="Choose a password" id="pass" type="password" value={f.password} onChange={set("password")} />
        <button type="submit" disabled={busy} className="btn-primary w-full">
          {busy ? "Activating…" : "Activate"}
        </button>
        <button type="button" onClick={() => navigate("/")} className="btn-ghost w-full">
          Back to home
        </button>
      </form>
    </AuthLayout>
  );
}
