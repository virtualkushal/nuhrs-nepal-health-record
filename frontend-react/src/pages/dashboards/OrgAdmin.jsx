import { useEffect, useState } from "react";
import { api, currentUser } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card, Table, Field, FieldError, FormBanner } from "../../components/ui.jsx";
import { parseApiError } from "../../lib/formErrors.js";
import UserChangePassword from "../../components/UserChangePassword.jsx";

const STAFF_TABS = [
  { id: "staff", label: "Staff" },
  { id: "facility", label: "Facility" },
  { id: "analytics", label: "Analytics" },
  { id: "audit", label: "Audit" },
  { id: "settings", label: "Account Settings" },
];

// Organization admin: run day-to-day facility operations — staff logins,
// facility contact details, facility-scoped analytics and the facility's
// own audit trail. Everything here is enforced server-side to own-org scope.
export default function OrgAdmin() {
  const user = currentUser();
  const [tab, setTab] = useState("staff");
  return (
    <div className="space-y-stack-lg">
      <div className="flex gap-2 border-b border-outline-variant">
        {STAFF_TABS.map((t) => (
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

      {tab === "staff" && <Staff orgName={user?.organization_name} />}
      {tab === "facility" && <Facility />}
      {tab === "analytics" && <FacilityAnalytics />}
      {tab === "audit" && <OrgAudit />}
      {tab === "settings" && (
        <Card title="Account Settings">
          <UserChangePassword />
        </Card>
      )}
    </div>
  );
}

// --- Staff ------------------------------------------------------------------
function Staff({ orgName }) {
  const { show } = useToast();
  const [staff, setStaff] = useState(null);
  const [creds, setCreds] = useState(null);
  const [resetPw, setResetPw] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({ full_name: "", email: "" });
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

  async function toggleActive(s) {
    const verb = s.is_active ? "deactivate" : "reactivate";
    if (!window.confirm(`${verb.charAt(0).toUpperCase() + verb.slice(1)} ${s.full_name || s.username}?`)) return;
    try {
      await api.updateStaff(s.id, { is_active: !s.is_active });
      show(`Staff ${verb}d`, "ok");
      load();
    } catch (e) {
      show(e.message, "err");
    }
  }

  async function resetPassword(s) {
    try {
      setResetPw(await api.resetUserPassword(s.id));
    } catch (e) {
      show(e.message, "err");
    }
  }

  function startEdit(s) {
    setEditingId(s.id);
    setDraft({ full_name: s.full_name || "", email: s.email || "" });
  }

  async function saveEdit(id) {
    try {
      await api.updateStaff(id, draft);
      show("Profile updated", "ok");
      setEditingId(null);
      load();
    } catch (e) {
      show(e.message, "err");
    }
  }

  return (
    <Card
      title={(orgName || "Organization") + " — Staff"}
      subtitle="Create logins for doctors and lab technicians, deactivate leavers, reset passwords."
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
      {resetPw && (
        <div className="mt-4 p-4 rounded-xl bg-ok/5 border border-ok/30 font-mono text-sm">
          <div className="font-semibold text-ok mb-2">Password reset ✔ (shown once)</div>
          User: {resetPw.login_name || resetPw.username}
          <br />
          Temp password: {resetPw.temporary_password}
        </div>
      )}

      <div className="mt-6">
        {!staff ? (
          <p className="text-on-surface-variant">Loading staff…</p>
        ) : (
          <Table head={["Username", "Name", "Role", "Status", "Actions"]}>
            {staff.length === 0 && (
              <tr><td colSpan={5} className="py-3 text-on-surface-variant">No staff yet</td></tr>
            )}
            {staff.map((s) => (
              <tr key={s.id} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{s.username}</td>
                {editingId === s.id ? (
                  <>
                    <td className="py-2 pr-4">
                      <input
                        className="field"
                        value={draft.full_name}
                        onChange={(e) => setDraft((d) => ({ ...d, full_name: e.target.value }))}
                      />
                    </td>
                    <td className="py-2 pr-4">{s.role}</td>
                    <td className="py-2 pr-4">{s.is_active ? "Active" : "Disabled"}</td>
                    <td className="py-2 pr-4 flex gap-2">
                      <button onClick={() => saveEdit(s.id)} className="px-3 py-1.5 rounded-lg bg-ok/10 text-ok font-label-md text-label-sm">Save</button>
                      <button onClick={() => setEditingId(null)} className="px-3 py-1.5 rounded-lg bg-surface-container-low text-on-surface-variant font-label-md text-label-sm">Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="py-2 pr-4">{s.full_name || ""}</td>
                    <td className="py-2 pr-4">{s.role}</td>
                    <td className="py-2 pr-4">{s.is_active ? "Active" : "Disabled"}</td>
                    <td className="py-2 pr-4">
                      <div className="flex flex-wrap gap-2">
                        {s.is_active ? (
                          <button onClick={() => toggleActive(s)} className="px-3 py-1.5 rounded-lg bg-error/10 text-error font-label-md text-label-sm">Deactivate</button>
                        ) : (
                          <button onClick={() => toggleActive(s)} className="px-3 py-1.5 rounded-lg bg-ok/10 text-ok font-label-md text-label-sm">Reactivate</button>
                        )}
                        <button onClick={() => resetPassword(s)} className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary font-label-md text-label-sm">Reset PW</button>
                        <button onClick={() => startEdit(s)} className="px-3 py-1.5 rounded-lg bg-surface-container-low text-on-surface-variant font-label-md text-label-sm">Edit</button>
                      </div>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </Table>
        )}
      </div>
    </Card>
  );
}

// --- Facility ---------------------------------------------------------------
function Facility() {
  const { show } = useToast();
  const [org, setOrg] = useState(null);
  const [form, setForm] = useState({ contact_email: "", contact_phone: "" });

  useEffect(() => {
    api.getFacility().then((o) => {
      setOrg(o);
      setForm({ contact_email: o.contact_email || "", contact_phone: o.contact_phone || "" });
    }).catch((e) => show(e.message, "err"));
  }, []);

  async function save(e) {
    e.preventDefault();
    try {
      const updated = await api.updateFacility(form);
      setOrg(updated);
      show("Facility contact updated", "ok");
    } catch (e2) {
      show(e2.message, "err");
    }
  }

  return (
    <Card title="Facility Details">
      {!org ? (
        <p className="text-on-surface-variant">Loading facility…</p>
      ) : (
        <form onSubmit={save} className="space-y-4 max-w-2xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Organization</label>
              <div className="field bg-surface-container-low cursor-not-allowed select-none">{org.organization_name}</div>
            </div>
            <div>
              <label className="label">Org code</label>
              <div className="field bg-surface-container-low cursor-not-allowed select-none">{org.organization_code || "—"}</div>
            </div>
            <Field label="Contact email" id="fac-email" value={form.contact_email} onChange={(v) => setForm((s) => ({ ...s, contact_email: v }))} />
            <Field label="Contact phone" id="fac-phone" value={form.contact_phone} onChange={(v) => setForm((s) => ({ ...s, contact_phone: v }))} />
          </div>
          <button type="submit" className="btn-primary">Save changes</button>
        </form>
      )}
    </Card>
  );
}

// --- Analytics --------------------------------------------------------------
function FacilityAnalytics() {
  const { show } = useToast();
  const [a, setA] = useState(null);
  useEffect(() => {
    api.facilityAnalytics().then(setA).catch((e) => show(e.message, "err"));
  }, []);

  if (!a) return <Card title="Facility Analytics"><p className="text-on-surface-variant">Loading analytics…</p></Card>;

  const stat = (n, l) => (
    <div className="p-stack-lg bg-surface-container-low rounded-xl text-center">
      <div className="font-display-lg text-[32px] text-primary tabular-nums">{n}</div>
      <div className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">{l}</div>
    </div>
  );

  return (
    <div className="space-y-stack-lg">
      <Card title={`${a.organization_name} — Facility Analytics`}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stat(a.records_indexed, "Records Indexed")}
          {stat(a.fetches_by_my_staff, "Fetches by Staff")}
          {stat(a.fetches_of_my_records, "Fetches of Records")}
          {stat(a.staff_by_role?.reduce((n, r) => n + r.count, 0) || 0, "Accounts")}
        </div>
      </Card>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
        <Card title="Indexed Records by Type">
          <Table head={["Resource", "Count"]}>
            {(a.by_resource_type || []).map((r, i) => (
              <tr key={i} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{r.resource_type}</td>
                <td className="py-2 pr-4">{r.count}</td>
              </tr>
            ))}
            {(!a.by_resource_type || a.by_resource_type.length === 0) && (
              <tr><td colSpan={2} className="py-3 text-on-surface-variant">No data</td></tr>
            )}
          </Table>
        </Card>
        <Card title="Accounts by Role">
          <Table head={["Role", "Count"]}>
            {(a.staff_by_role || []).map((r, i) => (
              <tr key={i} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{r.role.replace("_", " ")}</td>
                <td className="py-2 pr-4">{r.count}</td>
              </tr>
            ))}
            {(!a.staff_by_role || a.staff_by_role.length === 0) && (
              <tr><td colSpan={2} className="py-3 text-on-surface-variant">No data</td></tr>
            )}
          </Table>
        </Card>
      </div>
    </div>
  );
}

// --- Audit -------------------------------------------------------------------
function OrgAudit() {
  const { show } = useToast();
  const [logs, setLogs] = useState(null);
  const [nidFilter, setNidFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");

  const load = async () => {
    try {
      const filters = {};
      if (nidFilter) filters.nid = nidFilter;
      if (actionFilter) filters.action = actionFilter;
      setLogs(await api.audit(filters));
    } catch (e) {
      show(e.message, "err");
    }
  };
  useEffect(() => {
    load();
  }, [nidFilter, actionFilter]);

  return (
    <Card title="Facility Audit Trail" subtitle="Searches and fetches performed by your facility's accounts.">
      <div className="mb-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="label">Patient NID</label>
          <input
            className="field"
            value={nidFilter}
            onChange={(e) => setNidFilter(e.target.value)}
            placeholder="filter by NID"
          />
        </div>
        <div>
          <label className="label">Action</label>
          <select className="field" value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
            <option value="">All actions</option>
            <option value="SEARCH">Search</option>
            <option value="FETCH_ALL">Fetch All</option>
            <option value="FETCH_ONE">Fetch One</option>
            <option value="STAFF_DEACTIVATE">Staff Deactivated</option>
            <option value="STAFF_REACTIVATE">Staff Reactivated</option>
            <option value="STAFF_UPDATE">Staff Updated</option>
            <option value="ORG_UPDATE">Organization Updated</option>
            <option value="PASSWORD_RESET">Password Reset</option>
          </select>
        </div>
      </div>
      {!logs ? (
        <p className="text-on-surface-variant">Loading audit log…</p>
      ) : (
        <Table head={["Time", "Actor", "Action", "Patient NID", "Sources"]}>
          {logs.length === 0 && (
            <tr><td colSpan={5} className="py-3 text-on-surface-variant">No activity yet</td></tr>
          )}
          {logs.map((l, i) => (
            <tr key={i} className="border-b border-outline-variant/60">
              <td className="py-2 pr-4">{new Date(l.timestamp).toLocaleString()}</td>
              <td className="py-2 pr-4">
                {l.actor_username || "—"}
                <div className="text-label-sm text-on-surface-variant">{l.actor_org_name || ""}</div>
              </td>
              <td className="py-2 pr-4">{l.action}</td>
              <td className="py-2 pr-4">{l.nid || "—"}</td>
              <td className="py-2 pr-4">{l.target_orgs || "—"}</td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}
