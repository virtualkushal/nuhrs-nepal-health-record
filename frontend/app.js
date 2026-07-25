// NUHRS single-page app. Renders role-specific dashboards against the platform API.
const app = document.getElementById("app");

// ------------------------------------------------------------------ helpers
function toast(msg, kind = "") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = `toast ${kind}`;
  setTimeout(() => (t.className = "toast hidden"), 3200);
}

function el(html) {
  const d = document.createElement("div");
  d.innerHTML = html.trim();
  return d.firstElementChild;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
  );
}

function renderSession() {
  const user = API.currentUser();
  const sess = document.getElementById("session");
  if (user) {
    sess.classList.remove("hidden");
    document.getElementById("whoami").textContent = `${user.full_name || user.username} · ${user.role}`;
  } else {
    sess.classList.add("hidden");
  }
}

document.getElementById("logoutBtn").onclick = () => {
  API.clear();
  route();
};

// ------------------------------------------------------------------ routing
function route() {
  renderSession();
  const user = API.currentUser();
  if (!user) return renderLogin();
  if (user.must_change_password) return renderChangePassword();
  switch (user.role) {
    case "SUPER_ADMIN": return renderSuperAdmin();
    case "ORGANIZATION_ADMIN": return renderOrgAdmin();
    case "DOCTOR":
    case "LAB_TECHNICIAN": return renderExchange();
    case "PATIENT": return renderPatientPortal();
    default: return renderLogin();
  }
}

// ------------------------------------------------------------------ login
function renderLogin() {
  app.innerHTML = "";
  const card = el(`
    <div class="auth-wrap">
      <div class="card">
        <h2>Sign in</h2>
        <p class="muted">Health worker, administrator, or patient login.</p>
        <label>Username / NID</label>
        <input id="u" placeholder="e.g. superadmin or NID-1001" />
        <label>Password</label>
        <input id="p" type="password" placeholder="Password" />
        <button class="btn" id="loginBtn" style="width:100%">Sign in</button>
        <hr style="margin:20px 0;border:none;border-top:1px solid var(--line)" />
        <div class="grid cols-2">
          <button class="btn secondary small" id="orgRegBtn">Register Organization</button>
          <button class="btn small" id="patientActBtn">Activate Patient Account</button>
        </div>
        <p class="muted" style="margin-top:16px">
          Demo: <code>superadmin / admin123</code>
        </p>
      </div>
    </div>
  `);
  app.appendChild(card);
  card.querySelector("#loginBtn").onclick = doLogin;
  card.querySelector("#orgRegBtn").onclick = renderOrgRegister;
  card.querySelector("#patientActBtn").onclick = renderPatientActivate;
  card.querySelector("#p").addEventListener("keydown", (e) => {
    if (e.key === "Enter") doLogin();
  });
}

async function doLogin() {
  try {
    const username = document.getElementById("u").value.trim();
    const password = document.getElementById("p").value;
    const data = await API.login(username, password);
    API.setSession(data);
    toast("Welcome back", "ok");
    route();
  } catch (e) {
    toast(e.message, "err");
  }
}

function renderChangePassword() {
  app.innerHTML = "";
  const card = el(`
    <div class="auth-wrap"><div class="card">
      <h2>Set a new password</h2>
      <p class="muted">Your account uses a temporary password. Please change it.</p>
      <label>New password</label>
      <input id="np" type="password" />
      <button class="btn" id="cpBtn" style="width:100%">Update password</button>
    </div></div>
  `);
  app.appendChild(card);
  card.querySelector("#cpBtn").onclick = async () => {
    try {
      await API.changePassword(document.getElementById("np").value);
      const u = API.currentUser();
      u.must_change_password = false;
      localStorage.setItem("nuhrs_user", JSON.stringify(u));
      toast("Password updated", "ok");
      route();
    } catch (e) {
      toast(e.message, "err");
    }
  };
}

// ------------------------------------------------------------------ org register
function renderOrgRegister() {
  app.innerHTML = "";
  const card = el(`
    <div class="auth-wrap"><div class="card">
      <h2>Register Organization</h2>
      <p class="muted">Submit for Ministry approval. You'll receive credentials once approved.</p>
      <label>Organization name</label><input id="name" />
      <label>Type</label>
      <select id="type"><option value="HOSPITAL">Hospital</option><option value="LAB">Laboratory</option></select>
      <label>License number</label><input id="lic" />
      <label>FHIR API base URL</label><input id="url" placeholder="http://hospital-x:8001/fhir" />
      <div class="grid cols-2">
        <div><label>Contact email</label><input id="email" /></div>
        <div><label>Contact phone</label><input id="phone" /></div>
      </div>
      <div class="grid cols-2">
        <div><label>District</label><input id="district" /></div>
        <div><label>Province</label><input id="province" /></div>
      </div>
      <button class="btn" id="submit" style="width:100%">Submit registration</button>
      <button class="btn ghost small" id="back" style="width:100%;margin-top:8px;color:var(--muted)">Back to login</button>
    </div></div>
  `);
  app.appendChild(card);
  card.querySelector("#back").onclick = renderLogin;
  card.querySelector("#submit").onclick = async () => {
    try {
      await API.registerOrg({
        organization_name: val("name"),
        organization_type: val("type"),
        license_number: val("lic"),
        api_base_url: val("url"),
        contact_email: val("email"),
        contact_phone: val("phone"),
        district: val("district"),
        province: val("province"),
      });
      toast("Registration submitted for approval", "ok");
      renderLogin();
    } catch (e) {
      toast(e.message, "err");
    }
  };
}

// ------------------------------------------------------------------ patient activate
function renderPatientActivate() {
  app.innerHTML = "";
  const card = el(`
    <div class="auth-wrap"><div class="card">
      <h2>Activate Patient Account</h2>
      <p class="muted">Verify your identity to access your own records.</p>
      <label>National ID (NID)</label><input id="nid" placeholder="NID-1001" />
      <label>Date of birth</label><input id="dob" type="date" />
      <label>Phone</label><input id="phone" placeholder="9841000001" />
      <label>Choose a password</label><input id="pass" type="password" />
      <button class="btn" id="submit" style="width:100%">Activate</button>
      <button class="btn ghost small" id="back" style="width:100%;margin-top:8px;color:var(--muted)">Back to login</button>
    </div></div>
  `);
  app.appendChild(card);
  card.querySelector("#back").onclick = renderLogin;
  card.querySelector("#submit").onclick = async () => {
    try {
      await API.activatePatient({
        nid: val("nid"), date_of_birth: val("dob"),
        phone: val("phone"), password: val("pass"),
      });
      toast("Account activated — you can now sign in", "ok");
      renderLogin();
    } catch (e) {
      toast(e.message, "err");
    }
  };
}

function val(id) { return document.getElementById(id).value.trim(); }

// ------------------------------------------------------------------ super admin
async function renderSuperAdmin() {
  app.innerHTML = "";
  const shell = el(`
    <div>
      <div class="tabs">
        <button class="tab active" data-t="orgs">Organizations</button>
        <button class="tab" data-t="analytics">National Analytics</button>
        <button class="tab" data-t="audit">Audit Log</button>
      </div>
      <div id="tabbody"></div>
    </div>
  `);
  app.appendChild(shell);
  shell.querySelectorAll(".tab").forEach((b) => {
    b.onclick = () => {
      shell.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      const t = b.dataset.t;
      if (t === "orgs") saOrgs();
      if (t === "analytics") saAnalytics();
      if (t === "audit") saAudit();
    };
  });
  saOrgs();
}

async function saOrgs() {
  const body = document.getElementById("tabbody");
  body.innerHTML = `<div class="card"><p class="muted">Loading organizations…</p></div>`;
  try {
    const orgs = await API.listOrgs();
    const rows = orgs.map((o) => `
      <tr>
        <td>${esc(o.organization_name)}<br><small class="muted">${esc(o.organization_code || "—")}</small></td>
        <td>${esc(o.organization_type)}</td>
        <td>${esc(o.district || "")}, ${esc(o.province || "")}</td>
        <td><span class="badge ${o.status}">${o.status}</span></td>
        <td class="row-actions">
          ${o.status === "PENDING"
            ? `<button class="btn ok small" data-approve="${o.id}">Approve</button>
               <button class="btn warn small" data-reject="${o.id}">Reject</button>`
            : "—"}
        </td>
      </tr>`).join("");
    body.innerHTML = `
      <div class="card">
        <h2>Provider Registry</h2>
        <table><thead><tr><th>Organization</th><th>Type</th><th>Location</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>${rows || `<tr><td colspan="5" class="muted">No organizations yet</td></tr>`}</tbody></table>
      </div>`;
    body.querySelectorAll("[data-approve]").forEach((b) => {
      b.onclick = async () => {
        try {
          const creds = await API.approveOrg(b.dataset.approve);
          showCreds(creds);
          saOrgs();
        } catch (e) { toast(e.message, "err"); }
      };
    });
    body.querySelectorAll("[data-reject]").forEach((b) => {
      b.onclick = async () => {
        try { await API.rejectOrg(b.dataset.reject); toast("Rejected"); saOrgs(); }
        catch (e) { toast(e.message, "err"); }
      };
    });
  } catch (e) { toast(e.message, "err"); }
}

function showCreds(creds) {
  const modal = el(`
    <div class="card">
      <h3>Organization approved ✔</h3>
      <p class="muted">Share these credentials securely. They are shown only once.</p>
      <div class="creds">
        Org code:      ${esc(creds.organization_code)}<br>
        Admin login:   ${esc(creds.admin_username)}<br>
        Temp password: ${esc(creds.temporary_password)}<br>
        API key:       ${esc(creds.api_key)}
      </div>
    </div>`);
  document.getElementById("tabbody").prepend(modal);
}

async function saAnalytics() {
  const body = document.getElementById("tabbody");
  body.innerHTML = `<div class="card"><p class="muted">Loading analytics…</p></div>`;
  try {
    const a = await API.analytics();
    const conditions = (a.top_conditions || [])
      .map((c) => `<tr><td>${esc(c.summary)}</td><td>${c.count}</td></tr>`).join("");
    const provinces = (a.records_by_province || [])
      .map((p) => `<tr><td>${esc(p["organization__province"] || "Unknown")}</td><td>${p.count}</td></tr>`).join("");
    body.innerHTML = `
      <div class="card">
        <h2>National Health Analytics</h2>
        <p class="muted">Aggregated from record metadata — a public-health benefit of unified records.</p>
        <div class="grid cols-4">
          <div class="stat"><div class="n">${a.total_patients}</div><div class="l">Patients</div></div>
          <div class="stat"><div class="n">${a.total_records_indexed}</div><div class="l">Records Indexed</div></div>
          <div class="stat"><div class="n">${a.total_organizations}</div><div class="l">Active Orgs</div></div>
          <div class="stat"><div class="n">${a.total_exchanges}</div><div class="l">Exchanges</div></div>
        </div>
      </div>
      <div class="grid cols-2">
        <div class="card"><h3>Top Diagnoses</h3><table><thead><tr><th>Condition</th><th>Count</th></tr></thead><tbody>${conditions || `<tr><td colspan="2" class="muted">No data</td></tr>`}</tbody></table></div>
        <div class="card"><h3>Records by Province</h3><table><thead><tr><th>Province</th><th>Count</th></tr></thead><tbody>${provinces || `<tr><td colspan="2" class="muted">No data</td></tr>`}</tbody></table></div>
      </div>`;
  } catch (e) { toast(e.message, "err"); }
}

async function saAudit() {
  const body = document.getElementById("tabbody");
  body.innerHTML = `<div class="card"><p class="muted">Loading audit log…</p></div>`;
  try {
    const logs = await API.audit();
    const rows = logs.map((l) => `
      <tr>
        <td>${new Date(l.timestamp).toLocaleString()}</td>
        <td>${esc(l.actor_username || "—")}<br><small class="muted">${esc(l.actor_org_name || "")}</small></td>
        <td>${esc(l.action)}</td>
        <td>${esc(l.nid)}</td>
        <td>${esc(l.target_orgs || "—")}</td>
      </tr>`).join("");
    body.innerHTML = `
      <div class="card">
        <h2>Access Audit Trail</h2>
        <p class="muted">Every record search and fetch is logged for accountability.</p>
        <table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Patient NID</th><th>Sources</th></tr></thead>
        <tbody>${rows || `<tr><td colspan="5" class="muted">No activity yet</td></tr>`}</tbody></table>
      </div>`;
  } catch (e) { toast(e.message, "err"); }
}

// ------------------------------------------------------------------ org admin
async function renderOrgAdmin() {
  app.innerHTML = "";
  const user = API.currentUser();
  const shell = el(`
    <div class="card">
      <h2>${esc(user.organization_name || "Organization")} — Staff</h2>
      <p class="muted">Create logins for doctors and lab technicians.</p>
      <div class="grid cols-4">
        <div><label>Full name</label><input id="sfName" /></div>
        <div><label>Email</label><input id="sfEmail" /></div>
        <div><label>Role</label><select id="sfRole"><option value="DOCTOR">Doctor</option><option value="LAB_TECHNICIAN">Lab Technician</option></select></div>
        <div style="display:flex;align-items:flex-end"><button class="btn" id="addStaff" style="width:100%">Add staff</button></div>
      </div>
      <div id="staffCreds"></div>
      <div id="staffList"></div>
    </div>
  `);
  app.appendChild(shell);
  shell.querySelector("#addStaff").onclick = async () => {
    try {
      const res = await API.createStaff({
        full_name: val("sfName"), email: val("sfEmail"), role: val("sfRole"),
      });
      document.getElementById("staffCreds").innerHTML =
        `<div class="creds">New login: ${esc(res.username)} &nbsp; Temp password: ${esc(res.temporary_password)}</div>`;
      loadStaff();
    } catch (e) { toast(e.message, "err"); }
  };
  loadStaff();
}

async function loadStaff() {
  try {
    const staff = await API.listStaff();
    const rows = staff.map((s) => `
      <tr><td>${esc(s.username)}</td><td>${esc(s.full_name || "")}</td><td>${esc(s.role)}</td>
      <td>${s.is_active ? "Active" : "Disabled"}</td></tr>`).join("");
    document.getElementById("staffList").innerHTML = `
      <table style="margin-top:18px"><thead><tr><th>Username</th><th>Name</th><th>Role</th><th>Status</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="4" class="muted">No staff yet</td></tr>`}</tbody></table>`;
  } catch (e) { toast(e.message, "err"); }
}

// ------------------------------------------------------------------ exchange (doctor)
function renderExchange() {
  app.innerHTML = "";
  const shell = el(`
    <div>
      <div class="card">
        <h2>Patient Record Exchange</h2>
        <p class="muted">Search by National ID to retrieve a unified record from every participating facility.</p>
        <div class="grid cols-4">
          <div style="grid-column: span 3"><input id="nid" placeholder="Enter patient NID e.g. NID-1001" /></div>
          <div><button class="btn" id="searchBtn" style="width:100%">Search</button></div>
        </div>
      </div>
      <div id="result"></div>
    </div>
  `);
  app.appendChild(shell);
  shell.querySelector("#searchBtn").onclick = doSearch;
  shell.querySelector("#nid").addEventListener("keydown", (e) => { if (e.key === "Enter") doSearch(); });
}

async function doSearch() {
  const nid = val("nid");
  const result = document.getElementById("result");
  result.innerHTML = `<div class="card"><p class="muted">Searching national index…</p></div>`;
  try {
    const patient = await API.lookupPatient(nid);
    const index = await API.patientIndex(nid);
    const indexRows = index.map((r) => `
      <tr>
        <td>${esc(r.resource_type)}</td>
        <td>${esc(r.summary)}</td>
        <td><span class="badge src">${esc(r.organization_name)}</span></td>
        <td>${esc(r.service_date)}</td>
      </tr>`).join("");
    result.innerHTML = `
      <div class="card">
        <h3>${esc(patient.full_name)} <small class="muted">${esc(patient.nid)}</small></h3>
        <p class="muted">DOB ${esc(patient.date_of_birth)} · ${esc(patient.gender)} · ${esc(patient.phone || "")}</p>
        <table><thead><tr><th>Type</th><th>Summary</th><th>Source</th><th>Date</th></tr></thead>
        <tbody>${indexRows || `<tr><td colspan="4" class="muted">No records indexed</td></tr>`}</tbody></table>
        <div style="margin-top:16px">
          <button class="btn" id="fetchAll">Fetch full unified record</button>
        </div>
      </div>
      <div id="bundle"></div>`;
    document.getElementById("fetchAll").onclick = () => fetchBundle(nid);
  } catch (e) {
    result.innerHTML = `<div class="card"><p class="muted">${esc(e.message)}</p></div>`;
  }
}

async function fetchBundle(nid) {
  const bundle = document.getElementById("bundle");
  bundle.innerHTML = `<div class="card"><p class="muted">Routing engine contacting source facilities…</p></div>`;
  try {
    const data = await API.fetchRecords(nid, "ALL");
    const cards = (data.entry || []).map((e) => renderResource(e.resource)).join("");
    bundle.innerHTML = `
      <div class="card">
        <h3>Unified Clinical Record <small class="muted">${data.total} resource(s)</small></h3>
        ${cards || `<p class="muted">No clinical data returned.</p>`}
      </div>`;
  } catch (e) { toast(e.message, "err"); }
}

function renderResource(r) {
  const src = r._source ? `<span class="badge src">${esc(r._source)}</span>` : "";
  const type = r.resourceType;
  let title = type, detail = "";
  if (type === "Condition") {
    title = "Diagnosis: " + (r.code?.text || "—");
    detail = `ICD: ${esc(r.code?.coding?.[0]?.code || "—")} · onset ${esc(r.onsetDateTime || "—")}`;
  } else if (type === "Observation") {
    title = (r.code?.text || "Observation");
    detail = `${esc(r.valueQuantity?.value ?? "")} ${esc(r.valueQuantity?.unit ?? "")} · ${esc(r.effectiveDateTime || "")}`;
  } else if (type === "DiagnosticReport") {
    const results = (r.contained || [])
      .map((o) => `<li>${esc(o.code?.text)}: ${esc(o.valueQuantity?.value)} ${esc(o.valueQuantity?.unit)} <span class="muted">(${esc(o.referenceRange?.[0]?.text || "")})</span></li>`)
      .join("");
    title = "Lab Report: " + (r.code?.text || "—");
    detail = `${esc(r.effectiveDateTime || "")} · ${esc(r.conclusion || "")}<ul>${results}</ul>`;
  } else if (type === "Encounter") {
    title = "Encounter: " + (r.reasonCode?.[0]?.text || r.class?.code || "—");
    detail = `${esc(r.period?.start || "")} · ${esc(r.participant?.[0]?.individual?.display || "")}`;
  } else if (type === "Patient") {
    return ""; // identity already shown in the header
  } else if (type === "OperationOutcome") {
    return `<div class="record" style="border-left-color:var(--warn)">
      <h4>Source unavailable ${src}</h4>
      <div class="meta">${esc(r.issue?.[0]?.diagnostics || "")}</div></div>`;
  }
  return `<div class="record"><h4>${esc(title)} ${src}</h4><div class="meta">${detail}</div></div>`;
}

// ------------------------------------------------------------------ patient portal
async function renderPatientPortal() {
  app.innerHTML = `<div class="card"><p class="muted">Loading your records…</p></div>`;
  try {
    const data = await API.myRecords();
    const p = data.patient;
    const rows = data.records.map((r) => `
      <tr><td>${esc(r.resource_type)}</td><td>${esc(r.summary)}</td>
      <td><span class="badge src">${esc(r.organization_name)}</span></td><td>${esc(r.service_date)}</td></tr>`).join("");
    app.innerHTML = `
      <div class="card">
        <h2>My Health Record</h2>
        <h3>${esc(p.full_name)} <small class="muted">${esc(p.nid)}</small></h3>
        <p class="muted">DOB ${esc(p.date_of_birth)} · ${esc(p.gender)}</p>
        <table><thead><tr><th>Type</th><th>Summary</th><th>Facility</th><th>Date</th></tr></thead>
        <tbody>${rows || `<tr><td colspan="4" class="muted">No records yet</td></tr>`}</tbody></table>
      </div>`;
  } catch (e) { toast(e.message, "err"); }
}

// boot
route();
