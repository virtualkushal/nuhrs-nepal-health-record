import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api.js";
import { useToast } from "../context/ToastContext.jsx";
import { Field, FieldError, FormBanner } from "../components/ui.jsx";
import { parseApiError } from "../lib/formErrors.js";
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
  // Per-field validation errors (keyed by serializer field name) + a top-level
  // banner message for anything not tied to a single field.
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const set = (k) => (v) => setF((s) => ({ ...s, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setFormError("");
    try {
      await api.registerOrg(f);
      show("Registration submitted for approval", "ok");
      navigate("/");
    } catch (err) {
      const { fieldErrors, formError } = parseApiError(err);
      setErrors(fieldErrors);
      setFormError(formError);
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
        <FormBanner message={formError} />
        <Field label="Organization name" id="name" value={f.organization_name} onChange={set("organization_name")} error={errors.organization_name} />
        <div>
          <label className="label" htmlFor="orgtype">Type</label>
          <select id="orgtype" className={`field ${errors.organization_type ? "field-error" : ""}`} value={f.organization_type} onChange={(e) => set("organization_type")(e.target.value)}>
            <option value="HOSPITAL">Hospital</option>
            <option value="LAB">Laboratory</option>
          </select>
          <FieldError id="orgtype-error">{errors.organization_type}</FieldError>
        </div>
        <Field label="License number" id="lic" value={f.license_number} onChange={set("license_number")} error={errors.license_number} />
        <Field label="FHIR API base URL" id="url" value={f.api_base_url} onChange={set("api_base_url")} placeholder="http://hospital-x:8001/fhir" error={errors.api_base_url} />
        <div className="grid grid-cols-2 gap-4">
          <Field label="Contact email" id="email" value={f.contact_email} onChange={set("contact_email")} error={errors.contact_email} />
          <Field label="Contact phone" id="phone" value={f.contact_phone} onChange={set("contact_phone")} error={errors.contact_phone} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Field label="District" id="district" value={f.district} onChange={set("district")} error={errors.district} />
          <Field label="Province" id="province" value={f.province} onChange={set("province")} error={errors.province} />
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
