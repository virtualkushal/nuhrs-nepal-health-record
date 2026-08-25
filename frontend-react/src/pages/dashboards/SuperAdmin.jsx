import { useEffect, useState } from "react";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card, Table, Badge, Field, FormBanner } from "../../components/ui.jsx";
import { parseApiError } from "../../lib/formErrors.js";
import AnnouncementsPanel from "../../components/admin/AnnouncementsPanel.jsx";
import AnalyticsPanel from "../../components/admin/AnalyticsPanel.jsx";

const TABS = [
  { id: "orgs", label: "Organizations" },
  { id: "users", label: "Users" },
  { id: "ministry", label: "Ministry Accounts" },
  { id: "announcements", label: "Announcements" },
  { id: "analytics", label: "National Analytics" },
  { id: "audit", label: "Audit Log" },
];

export default function SuperAdmin() {
  const [tab, setTab] = useState("orgs");
  return (
    <div className="space-y-stack-lg">
      <div className="flex gap-2 border-b border-outline-variant">
        {TABS.map((t) => (
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
      {tab === "orgs" && <Orgs />}
      {tab === "users" && <Users />}
      {tab === "ministry" && <MinistryAccounts />}
      {tab === "announcements" && <AnnouncementsPanel />}
      {tab === "analytics" && <AnalyticsPanel />}
      {tab === "audit" && <Audit />}
    </div>
  );
}

function Orgs() {
  const { show } = useToast();
  const [orgs, setOrgs] = useState(null);
  const [creds, setCreds] = useState(null);

  const load = async () => {
    try {
      setOrgs(await api.listOrgs());
    } catch (e) {
      show(e.message, "err");
    }
  };
  useEffect(() => {
    load();
  }, []);

  async function approve(id) {
    try {
      setCreds(await api.approveOrg(id));
      load();
    } catch (e) {
      show(e.message, "err");
    }
  }
  async function reject(id) {
    try {
      await api.rejectOrg(id);
      show("Rejected");
      load();
    } catch (e) {
      show(e.message, "err");
    }
  }
  async function suspend(id) {
    try {
      await api.suspendOrganization(id);
      show("Organization suspended");
      load();
    } catch (e) {
      show(e.message, "err");
    }
  }
  async function reactivate(id) {
    try {
      await api.reactivateOrganization(id);
      show("Organization reactivated");
      load();
    } catch (e) {
      show(e.message, "err");
    }
  }

  return (
    <Card title="Provider Registry">
      {creds && (
        <div className="mb-6 p-4 rounded-xl bg-ok/5 border border-ok/30 font-mono text-sm text-on-surface">
          <div className="font-semibold text-ok mb-2">Organization approved ✔ (shown once)</div>
          Org code: {creds.organization_code}
          <br />
          Admin login: {creds.admin_username}
          <br />
          Temp password: {creds.temporary_password}
          <br />
          API key: {creds.api_key}
        </div>
      )}
      {!orgs ? (
        <p className="text-on-surface-variant">Loading organizations…</p>
      ) : (
        <Table head={["Organization", "Type", "Location", "Status", "Action"]}>
          {orgs.length === 0 && (
            <tr>
              <td colSpan={5} className="py-4 text-on-surface-variant">
                No organizations yet
              </td>
            </tr>
          )}
          {orgs.map((o) => (
            <tr key={o.id} className="border-b border-outline-variant/60">
              <td className="py-3 pr-4">
                {o.organization_name}
                <div className="text-label-sm text-on-surface-variant">
                  {o.organization_code || "—"}
                </div>
              </td>
              <td className="py-3 pr-4">{o.organization_type}</td>
              <td className="py-3 pr-4">
                {(o.district || "") + ", " + (o.province || "")}
              </td>
              <td className="py-3 pr-4">
                <Badge tone={o.status}>{o.status}</Badge>
              </td>
              <td className="py-3 pr-4">
                {o.status === "PENDING" ? (
                  <div className="flex gap-2">
                    <button onClick={() => approve(o.id)} className="px-3 py-1.5 rounded-lg bg-ok/10 text-ok font-label-md text-label-sm">
                      Approve
                    </button>
                    <button onClick={() => reject(o.id)} className="px-3 py-1.5 rounded-lg bg-error/10 text-error font-label-md text-label-sm">
                      Reject
                    </button>
                  </div>
                ) : o.status === "ACTIVE" ? (
                  <button onClick={() => suspend(o.id)} className="px-3 py-1.5 rounded-lg bg-error/10 text-error font-label-md text-label-sm">
                    Suspend
                  </button>
                ) : o.status === "SUSPENDED" ? (
                  <button onClick={() => reactivate(o.id)} className="px-3 py-1.5 rounded-lg bg-ok/10 text-ok font-label-md text-label-sm">
                    Reactivate
                  </button>
                ) : (
                  "—"
                )}
              </td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}

const ROLE_OPTIONS = [
  { value: "", label: "All roles" },
  { value: "ORGANIZATION_ADMIN", label: "Org Admin" },
  { value: "DOCTOR", label: "Doctor" },
  { value: "LAB_TECHNICIAN", label: "Lab Technician" },
  { value: "PATIENT", label: "Patient" },
  { value: "MINISTRY", label: "Ministry" },
  { value: "SUPER_ADMIN", label: "Super Admin" },
];

function Users() {
  const { show } = useToast();
  const [users, setUsers] = useState(null);
  const [roleFilter, setRoleFilter] = useState("");
  const [reset, setReset] = useState(null);

  const load = async () => {
    try {
      const filters = roleFilter ? { role: roleFilter } : undefined;
      setUsers(await api.getAllUsers(filters));
    } catch (e) {
      show(e.message, "err");
    }
  };
  useEffect(() => {
    load();
  }, [roleFilter]);

  async function resetPassword(id) {
    try {
      setReset(await api.resetUserPassword(id));
    } catch (e) {
      show(e.message, "err");
    }
  }

  return (
    <Card title="User Management" subtitle="View every account and reset passwords across all organizations.">
      {reset && (
        <div className="mb-6 p-4 rounded-xl bg-ok/5 border border-ok/30 font-mono text-sm text-on-surface">
          <div className="font-semibold text-ok mb-2">Password reset ✔ (shown once)</div>
          User: {reset.login_name || reset.username}
          <br />
          Temp password: {reset.temporary_password}
        </div>
      )}
      <div className="mb-4">
        <select
          className="field max-w-xs"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
        >
          {ROLE_OPTIONS.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </div>
      {!users ? (
        <p className="text-on-surface-variant">Loading users…</p>
      ) : (
        <Table head={["Login", "Name", "Role", "Organization", "Active", "Action"]}>
          {users.length === 0 && (
            <tr><td colSpan={6} className="py-3 text-on-surface-variant">No users</td></tr>
          )}
          {users.map((u) => (
            <tr key={u.id} className="border-b border-outline-variant/60">
              <td className="py-3 pr-4">{u.login_name || u.username}</td>
              <td className="py-3 pr-4">{u.full_name || "—"}</td>
              <td className="py-3 pr-4">{u.role}</td>
              <td className="py-3 pr-4">{u.organization_name || "—"}</td>
              <td className="py-3 pr-4">
                <Badge tone={u.is_active ? "ACTIVE" : "SUSPENDED"}>
                  {u.is_active ? "Yes" : "No"}
                </Badge>
              </td>
              <td className="py-3 pr-4">
                <button
                  onClick={() => resetPassword(u.id)}
                  className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary font-label-md text-label-sm"
                >
                  Reset Password
                </button>
              </td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}

// Super-admin-only power: mint and revoke Ministry accounts. Mirrors the
// org-approval "show the temp password once" flow. Ministry itself cannot
// reach this — the backend gates create/list/delete to SUPER_ADMIN.
function MinistryAccounts() {
  const { show } = useToast();
  const [users, setUsers] = useState(null);
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [creds, setCreds] = useState(null);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");

  const load = async () => {
    try {
      setUsers(await api.listMinistryUsers());
    } catch (e) {
      show(e.message, "err");
    }
  };
  useEffect(() => {
    load();
  }, []);

  async function create(e) {
    e.preventDefault();
    setErrors({});
    setFormError("");
    if (!username.trim()) {
      setErrors({ username: "Username is required." });
      return;
    }
    setBusy(true);
    try {
      const res = await api.createMinistryUser({
        username: username.trim(),
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim(),
      });
      setCreds(res);
      show("Ministry account created", "ok");
      setUsername("");
      setFullName("");
      setEmail("");
      setPhone("");
      load();
    } catch (err) {
      const { fieldErrors, formError } = parseApiError(err);
      setErrors(fieldErrors);
      setFormError(formError);
    } finally {
      setBusy(false);
    }
  }

  async function remove(id) {
    try {
      await api.deleteMinistryUser(id);
      show("Ministry account deleted");
      load();
    } catch (e) {
      show(e.message, "err");
    }
  }

  return (
    <div className="space-y-stack-lg">
      <Card title="Create Ministry Account" subtitle="Ministry officials can broadcast announcements and view national analytics — nothing else.">
        {creds && (
          <div className="mb-6 p-4 rounded-xl bg-ok/5 border border-ok/30 font-mono text-sm text-on-surface">
            <div className="font-semibold text-ok mb-2">Ministry account created ✔ (password shown once)</div>
            Username: {creds.login_name || creds.username}
            <br />
            Temp password: {creds.temporary_password}
          </div>
        )}
        <form onSubmit={create} className="space-y-4 max-w-2xl">
          <FormBanner message={formError} />
          <Field label="Username" id="min-username" value={username} onChange={setUsername} placeholder="e.g. moh.official" error={errors.username} />
          <Field label="Full name" id="min-fullname" value={fullName} onChange={setFullName} placeholder="e.g. Ministry of Health & Population" error={errors.full_name} />
          <Field label="Email" id="min-email" type="email" value={email} onChange={setEmail} placeholder="official@mohp.gov.np" error={errors.email} />
          <Field label="Phone" id="min-phone" value={phone} onChange={setPhone} placeholder="01-5550000" error={errors.phone} />
          <button
            type="submit"
            disabled={busy}
            className="px-6 py-3 bg-primary text-on-primary rounded-lg disabled:opacity-50"
          >
            {busy ? "Creating…" : "Create Ministry Account"}
          </button>
        </form>
      </Card>

      <Card title="Ministry Accounts">
        {!users ? (
          <p className="text-on-surface-variant">Loading ministry accounts…</p>
        ) : (
          <Table head={["Username", "Name", "Email", "Active", "Action"]}>
            {users.length === 0 && (
              <tr><td colSpan={5} className="py-3 text-on-surface-variant">No ministry accounts yet</td></tr>
            )}
            {users.map((u) => (
              <tr key={u.id} className="border-b border-outline-variant/60">
                <td className="py-3 pr-4">{u.login_name || u.username}</td>
                <td className="py-3 pr-4">{u.full_name || "—"}</td>
                <td className="py-3 pr-4">{u.email || "—"}</td>
                <td className="py-3 pr-4">
                  <Badge tone={u.is_active ? "ACTIVE" : "SUSPENDED"}>
                    {u.is_active ? "Yes" : "No"}
                  </Badge>
                </td>
                <td className="py-3 pr-4">
                  <button
                    onClick={() => remove(u.id)}
                    className="px-3 py-1.5 rounded-lg bg-error/10 text-error font-label-md text-label-sm"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
}

function Audit() {
  const { show } = useToast();
  const [logs, setLogs] = useState(null);
  useEffect(() => {
    api.audit().then(setLogs).catch((e) => show(e.message, "err"));
  }, []);

  return (
    <Card title="Access Audit Trail" subtitle="Every record search and fetch is logged for accountability.">
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
              <td className="py-2 pr-4">{l.nid}</td>
              <td className="py-2 pr-4">{l.target_orgs || "—"}</td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}
