import { useEffect, useState } from "react";
import { api, currentUser } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card, Table, Field, FieldError, FormBanner } from "../../components/ui.jsx";
import { parseApiError } from "../../lib/formErrors.js";
import UserChangePassword from "../../components/UserChangePassword.jsx";

// Organization admin: create and list staff logins.
export default function OrgAdmin() {
  const { show } = useToast();
  const user = currentUser();
  const [tab, setTab] = useState("staff");
  const [staff, setStaff] = useState(null);
  const [creds, setCreds] = useState(null);
  const [f, setF] = useState({ full_name: "", email: "", role: "DOCTOR" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const set = (k) => (v) => setF((s) => ({ ...s, [k]: v }));

  const load = async () => {
    try {
      setStaff(await api.listStaff());
    } catch (e) {
      show(e.message, "err");
    }
  };
  useEffect(() => {
    load();
  }, []);

  async function addStaff(e) {
    e.preventDefault();
    setErrors({});
    setFormError("");
    try {
      const res = await api.createStaff(f);
      setCreds(res);
      setF({ full_name: "", email: "", role: "DOCTOR" });
      load();
    } catch (err) {
      const { fieldErrors, formError } = parseApiError(err);
      setErrors(fieldErrors);
      setFormError(formError);
    }
  }

  return (
    <div className="space-y-stack-lg">
      <div className="flex gap-2 border-b border-outline-variant">
        {[
          { id: "staff", label: "Staff" },
          { id: "settings", label: "Account Settings" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-3 font-label-md border-b-2 -mb-px transition-colors ${
              tab === t.id
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:text-primary"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "settings" ? (
        <Card title="Account Settings">
          <UserChangePassword />
        </Card>
      ) : (
        <Card
          title={(user?.organization_name || "Organization") + " — Staff"}
          subtitle="Create logins for doctors and lab technicians."
        >
      <form onSubmit={addStaff} className="space-y-4">
        <FormBanner message={formError} />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-start">
          <Field label="Full name" id="sfName" value={f.full_name} onChange={set("full_name")} error={errors.full_name} />
          <Field label="Email" id="sfEmail" value={f.email} onChange={set("email")} error={errors.email} />
          <div>
            <label className="label" htmlFor="sfRole">Role</label>
            <select
              id="sfRole"
              className={`field ${errors.role ? "field-error" : ""}`}
              value={f.role}
              onChange={(e) => set("role")(e.target.value)}
              aria-invalid={errors.role ? "true" : undefined}
              aria-describedby={errors.role ? "sfRole-error" : undefined}
            >
              <option value="DOCTOR">Doctor</option>
              <option value="LAB_TECHNICIAN">Lab Technician</option>
            </select>
            <FieldError id="sfRole-error">{errors.role}</FieldError>
          </div>
          <button type="submit" className="btn-primary md:mt-6">Add staff</button>
        </div>
      </form>

      {creds && (
        <div className="mt-4 p-4 rounded-xl bg-ok/5 border border-ok/30 font-mono text-sm">
          New login: {creds.username} &nbsp; Temp password: {creds.temporary_password}
        </div>
      )}

      <div className="mt-6">
        {!staff ? (
          <p className="text-on-surface-variant">Loading staff…</p>
        ) : (
          <Table head={["Username", "Name", "Role", "Status"]}>
            {staff.length === 0 && (
              <tr><td colSpan={4} className="py-3 text-on-surface-variant">No staff yet</td></tr>
            )}
            {staff.map((s) => (
              <tr key={s.username} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{s.username}</td>
                <td className="py-2 pr-4">{s.full_name || ""}</td>
                <td className="py-2 pr-4">{s.role}</td>
                <td className="py-2 pr-4">{s.is_active ? "Active" : "Disabled"}</td>
              </tr>
            ))}
          </Table>
        )}
      </div>
        </Card>
      )}
    </div>
  );
}
