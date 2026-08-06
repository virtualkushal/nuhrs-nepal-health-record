import { useEffect, useState } from "react";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card, Table, Badge } from "../../components/ui.jsx";

const TABS = [
  { id: "orgs", label: "Organizations" },
  { id: "users", label: "Users" },
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
      {tab === "analytics" && <Analytics />}
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

function Analytics() {
  const { show } = useToast();
  const [a, setA] = useState(null);
  useEffect(() => {
    api.analytics().then(setA).catch((e) => show(e.message, "err"));
  }, []);

  if (!a) return <Card title="National Health Analytics"><p className="text-on-surface-variant">Loading analytics…</p></Card>;

  const stat = (n, l) => (
    <div className="p-stack-lg bg-surface-container-low rounded-xl text-center">
      <div className="font-display-lg text-[32px] text-primary tabular-nums">{n}</div>
      <div className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">{l}</div>
    </div>
  );

  return (
    <div className="space-y-stack-lg">
      <Card title="National Health Analytics" subtitle="Aggregated from record metadata — a public-health benefit of unified records.">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stat(a.total_patients, "Patients")}
          {stat(a.total_records_indexed, "Records Indexed")}
          {stat(a.total_organizations, "Active Orgs")}
          {stat(a.total_exchanges, "Exchanges")}
        </div>
      </Card>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
        <Card title="Top Diagnoses">
          <Table head={["Condition", "Count"]}>
            {(a.top_conditions || []).map((c, i) => (
              <tr key={i} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{c.summary}</td>
                <td className="py-2 pr-4">{c.count}</td>
              </tr>
            ))}
            {(!a.top_conditions || a.top_conditions.length === 0) && (
              <tr><td colSpan={2} className="py-3 text-on-surface-variant">No data</td></tr>
            )}
          </Table>
        </Card>
        <Card title="Records by Province">
          <Table head={["Province", "Count"]}>
            {(a.records_by_province || []).map((p, i) => (
              <tr key={i} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{p["organization__province"] || "Unknown"}</td>
                <td className="py-2 pr-4">{p.count}</td>
              </tr>
            ))}
            {(!a.records_by_province || a.records_by_province.length === 0) && (
              <tr><td colSpan={2} className="py-3 text-on-surface-variant">No data</td></tr>
            )}
          </Table>
        </Card>
      </div>
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
