import { useState } from "react";
import { Loader2, X } from "lucide-react";
import { GENDER_OPTIONS, BLOOD_GROUPS, MARITAL_STATUS } from "../constants";

// Reusable patient demographics form (v2). Used by both public self-registration
// and receptionist intake. Allergies are free-text tags (shown to the doctor as
// a banner; no blocking). An optional email creates a portal login (a temporary
// password is emailed by the backend).
//
// Props:
//   onSubmit(payload) -> Promise    caller performs the actual API call
//   submitLabel                     text on the submit button
//   withCredentials                 when true, collect an email for a portal login
export default function PatientForm({
  onSubmit,
  submitLabel = "Register",
  withCredentials = false,
}) {
  const empty = {
    national_id: "",
    first_name: "",
    last_name: "",
    phone_number: "",
    date_of_birth: "",
    gender: "male",
    blood_group: "UNKNOWN",
    address: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    marital_status: "",
    occupation: "",
    email: "",
  };
  const [form, setForm] = useState(empty);
  const [allergies, setAllergies] = useState([]);
  const [allergyInput, setAllergyInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const update = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  function addAllergy() {
    const t = allergyInput.trim();
    if (t && !allergies.includes(t)) setAllergies((a) => [...a, t]);
    setAllergyInput("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const { email, ...demographics } = form;
      const payload = { ...demographics, allergies };
      if (withCredentials && email.trim()) payload.email = email.trim();
      await onSubmit(payload);
      setForm(empty);
      setAllergies([]);
    } catch (err) {
      const detail =
        err?.response?.data && typeof err.response.data === "object"
          ? Object.values(err.response.data).flat().join(" ")
          : "Something went wrong. Please check your entries and try again.";
      setError(detail);
    } finally {
      setBusy(false);
    }
  }

  const field =
    "w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500";
  const lbl = "block text-sm font-medium text-gray-200 mb-1";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>First name</label>
          <input className={field} value={form.first_name} onChange={(e) => update("first_name", e.target.value)} required />
        </div>
        <div>
          <label className={lbl}>Last name</label>
          <input className={field} value={form.last_name} onChange={(e) => update("last_name", e.target.value)} required />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>National ID</label>
          <input className={field} value={form.national_id} onChange={(e) => update("national_id", e.target.value)} placeholder="10–12 digits" required />
        </div>
        <div>
          <label className={lbl}>Phone number</label>
          <input className={field} value={form.phone_number} onChange={(e) => update("phone_number", e.target.value)} placeholder="+977-98XXXXXXXX" required />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className={lbl}>Date of birth</label>
          <input type="date" className={field} value={form.date_of_birth} onChange={(e) => update("date_of_birth", e.target.value)} required />
        </div>
        <div>
          <label className={lbl}>Gender</label>
          <select className={field} value={form.gender} onChange={(e) => update("gender", e.target.value)}>
            {GENDER_OPTIONS.map((g) => <option key={g.value} value={g.value}>{g.label}</option>)}
          </select>
        </div>
        <div>
          <label className={lbl}>Blood group</label>
          <select className={field} value={form.blood_group} onChange={(e) => update("blood_group", e.target.value)}>
            {BLOOD_GROUPS.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label className={lbl}>Address</label>
        <input className={field} value={form.address} onChange={(e) => update("address", e.target.value)} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>Emergency contact name</label>
          <input className={field} value={form.emergency_contact_name} onChange={(e) => update("emergency_contact_name", e.target.value)} />
        </div>
        <div>
          <label className={lbl}>Emergency contact phone</label>
          <input className={field} value={form.emergency_contact_phone} onChange={(e) => update("emergency_contact_phone", e.target.value)} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={lbl}>Marital status</label>
          <select className={field} value={form.marital_status} onChange={(e) => update("marital_status", e.target.value)}>
            {MARITAL_STATUS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        </div>
        <div>
          <label className={lbl}>Occupation</label>
          <input className={field} value={form.occupation} onChange={(e) => update("occupation", e.target.value)} />
        </div>
      </div>

      <div>
        <label className={lbl}>Known allergies</label>
        <div className="flex gap-2">
          <input
            className={field}
            value={allergyInput}
            onChange={(e) => setAllergyInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addAllergy(); } }}
            placeholder="Type an allergy and press Enter (e.g. Penicillin)"
          />
          <button type="button" onClick={addAllergy} className="rounded-lg bg-slate-800 px-4 text-sm font-semibold text-white hover:bg-slate-900">
            Add
          </button>
        </div>
        {allergies.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {allergies.map((a) => (
              <span key={a} className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-3 py-1 text-sm text-red-300 ring-1 ring-red-500/30">
                {a}
                <button type="button" onClick={() => setAllergies((cur) => cur.filter((x) => x !== a))}>
                  <X className="h-3.5 w-3.5" />
                </button>
              </span>
            ))}
          </div>
        )}
        <p className="mt-1 text-xs text-gray-500">Leave empty if the patient has no known allergies.</p>
      </div>

      {withCredentials && (
        <div className="rounded-lg border border-line bg-surface-700 p-4 space-y-2">
          <p className="text-sm font-medium text-gray-200">
            Create a portal login <span className="font-normal text-gray-500">(optional)</span>
          </p>
          <p className="text-xs text-gray-500">
            Enter an email to sign in later and view your records. A temporary password will be emailed. Leave blank to skip.
          </p>
          <input type="email" className={field} value={form.email} onChange={(e) => update("email", e.target.value)} placeholder="you@example.com" autoComplete="email" />
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm px-3 py-2">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={busy}
        className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-60 text-white font-medium rounded-lg px-4 py-2.5 transition-colors"
      >
        {busy && <Loader2 className="w-5 h-5 animate-spin" />}
        {busy ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}
