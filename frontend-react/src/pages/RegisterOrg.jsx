import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api.js";
import { useToast } from "../context/ToastContext.jsx";
import { Field } from "../components/ui.jsx";
import Brand from "../components/Brand.jsx";


// Public organization registration form.
export default function RegisterOrg() {
  const navigate = useNavigate();
  const { show } = useToast();
  const [f, setF] = useState({
    organization_name: "",
    organization_type: "HOSPITAL",
    license_number: "",
    api_base_url: "",
    contact_email: "",
    contact_phone: "",
    district: "",
    province: "",
  });
  const [busy, setBusy] = useState(false);
  const set = (k) => (v) => setF((s) => ({ ...s, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.registerOrg(f);
      show("Registration submitted for approval", "ok");
      navigate("/");
    } catch (err) {
      show(err.message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Register Organization"
      subtitle="Submit for Ministry approval. You'll receive credentials once approved."
    >
      <form className="space-y-5" onSubmit={submit}>
        <Field label="Organization name" id="name" value={f.organization_name} onChange={set("organization_name")} />
        <div>
          <label className="label">Type</label>
          <select className="field" value={f.organization_type} onChange={(e) => set("organization_type")(e.target.value)}>
            <option value="HOSPITAL">Hospital</option>
            <option value="LAB">Laboratory</option>
          </select>
        </div>
        <Field label="License number" id="lic" value={f.license_number} onChange={set("license_number")} />
        <Field label="FHIR API base URL" id="url" value={f.api_base_url} onChange={set("api_base_url")} placeholder="http://hospital-x:8001/fhir" />
        <div className="grid grid-cols-2 gap-4">
          <Field label="Contact email" id="email" value={f.contact_email} onChange={set("contact_email")} />
          <Field label="Contact phone" id="phone" value={f.contact_phone} onChange={set("contact_phone")} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Field label="District" id="district" value={f.district} onChange={set("district")} />
          <Field label="Province" id="province" value={f.province} onChange={set("province")} />
        </div>
        <button type="submit" disabled={busy} className="btn-primary w-full">
          {busy ? "Submitting…" : "Submit registration"}
        </button>
        <button type="button" onClick={() => navigate("/")} className="btn-ghost w-full">
          Back to home
        </button>
      </form>
    </AuthLayout>
  );
}

export function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="min-h-screen bg-background flex items-start justify-center px-margin-mobile pt-6 pb-12">

      <div className="w-full max-w-lg">
        <div className="flex items-center justify-center mb-6">
          <Brand size={32} />
        </div>
        <div className="panel">

          <h2 className="font-headline-lg text-[24px] text-on-surface">{title}</h2>
          {subtitle && <p className="text-body-md text-on-surface-variant mt-1 mb-6">{subtitle}</p>}
          {children}
        </div>
      </div>
    </div>
  );
}
