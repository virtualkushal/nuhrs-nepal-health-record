// Thin fetch wrapper around the National Platform API.
//
// Auth is carried by httpOnly cookies (access_token / refresh_token) set by the
// backend on login — never by JavaScript-readable tokens — so an XSS payload
// cannot exfiltrate a session. The SPA is served same-origin with the API via
// an /api proxy (Vite in dev, nginx in prod), which is why first-party cookies
// and a SameSite=Lax CSRF token work over plain http on localhost.
//
// Every request sends credentials; unsafe methods echo the csrftoken cookie in
// an X-CSRFToken header (double-submit). A 401 triggers one silent refresh +
// retry. Only the non-sensitive `user` object is mirrored into localStorage,
// purely so a hard refresh can render the right dashboard before the first API
// call returns.
const API_BASE = "/api";
const USER_KEY = "nuhrs_user";

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
// Auth endpoints must never trigger the refresh-on-401 retry (they either issue
// or depend on the very cookies a refresh would rotate — retrying loops).
const NO_REFRESH = new Set([
  "/auth/login/",
  "/auth/refresh/",
  "/auth/logout/",
  "/auth/csrf/",
  "/auth/sso-verify/",
]);

function getCookie(name) {
  const match = document.cookie.match(
    "(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)",
  );
  return match ? decodeURIComponent(match[1]) : null;
}

// Ensure a csrftoken cookie exists before the first state-changing request (and
// before a cold-start refresh). Cached after the first successful prime.
let csrfPrimed = false;
async function ensureCsrf() {
  if (csrfPrimed || getCookie("csrftoken")) {
    csrfPrimed = true;
    return;
  }
  try {
    await fetch(API_BASE + "/auth/csrf/", { credentials: "include" });
  } catch {
    /* offline / network error — the request itself will surface it */
  }
  csrfPrimed = true;
}

async function tryRefresh() {
  await ensureCsrf();
  const csrf = getCookie("csrftoken");
  try {
    const res = await fetch(API_BASE + "/auth/refresh/", {
      method: "POST",
      headers: csrf ? { "X-CSRFToken": csrf } : {},
      credentials: "include",
    });
    return res.ok;
  } catch {
    return false;
  }
}

// The `auth` flag no longer gates a token header (cookies are always sent); it
// only marks whether a 401 on this call should attempt a silent refresh.
async function request(method, path, body, auth = true) {
  const send = async () => {
    const headers = { "Content-Type": "application/json" };
    if (UNSAFE_METHODS.has(method)) {
      await ensureCsrf();
      const csrf = getCookie("csrftoken");
      if (csrf) headers["X-CSRFToken"] = csrf;
    }
    return fetch(API_BASE + path, {
      method,
      headers,
      credentials: "include",
      body: body ? JSON.stringify(body) : undefined,
    });
  };

  let res = await send();
  if (res.status === 401 && auth && !NO_REFRESH.has(path)) {
    if (await tryRefresh()) res = await send();
  }

  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) {
    const err = new Error(data.detail || `Request failed (${res.status})`);
    err.status = res.status;
    // Full DRF error object (field errors, non_field_errors, …) for the form
    // error parser — see lib/formErrors.js.
    err.data = data;
    throw err;
  }
  return data;
}

export function currentUser() {
  const raw = window.localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function saveUser(user) {
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  window.localStorage.removeItem(USER_KEY);
}

export const api = {
  // auth
  // Accepts a credentials object. Supported shapes:
  //   Staff:    { scope: "STAFF",    org_code, login_name, password }
  //   Patient:  { scope: "PATIENT",  username, password }   (username = NID)
  //   Official: { scope: "OFFICIAL", username, password }   (Super Admin or Ministry)
  // A bare { username, password } (no scope) still works (legacy path).
  // On success the server sets the httpOnly JWT cookies and returns { user }.
  login: (credentials) => request("POST", "/auth/login/", credentials, false),
  // Clear the session cookies server-side.
  logout: () => request("POST", "/auth/logout/", null, false),
  // Validate/refresh the current session and return the live user profile.
  me: () => request("GET", "/auth/me/"),
  // Redeem a single-use SSO ticket issued to a trusted facility (e.g. a doctor
  // arriving from SwasthyaEHR); the server sets the JWT cookies and returns { user }.
  ssoVerify: (ticket) =>
    request("POST", "/auth/sso-verify/", { ticket }, false),

  // current_password is optional — sent for user-initiated changes so the
  // server verifies the old password before applying the new one.
  changePassword: (new_password, current_password) =>
    request("POST", "/auth/change-password/", {
      new_password,
      current_password,
    }),
  // organizations
  registerOrg: (payload) => request("POST", "/orgs/register/", payload, false),
  listOrgs: (status) =>
    request("GET", `/orgs/${status ? "?status=" + status : ""}`),
  getActiveOrganizations: () => request("GET", "/orgs/active/", null, false),
  // public aggregate counters for the landing page stats band
  publicStats: () => request("GET", "/stats/public/", null, false),
  approveOrg: (id) => request("POST", `/orgs/${id}/approve/`),
  rejectOrg: (id) => request("POST", `/orgs/${id}/reject/`),
  suspendOrganization: (id) => request("POST", `/orgs/${id}/suspend/`),
  reactivateOrganization: (id) => request("POST", `/orgs/${id}/reactivate/`),
  // staff
  listStaff: () => request("GET", "/staff/"),
  createStaff: (payload) => request("POST", "/staff/", payload),
  // org-admin staff management (deactivate/reactivate + profile edit)
  updateStaff: (id, payload) => request("PATCH", `/staff/${id}/`, payload),
  // org-admin facility self-service
  getFacility: () => request("GET", "/facility/"),
  updateFacility: (payload) => request("PATCH", "/facility/", payload),
  // ministry user management
  getAllUsers: (filters) => {
    const qs = filters ? new URLSearchParams(filters).toString() : "";
    return request("GET", `/users/${qs ? "?" + qs : ""}`);
  },
  resetUserPassword: (userId) =>
    request("POST", `/users/${userId}/reset-password/`),
  // ministry accounts (super admin creates/lists/deletes the restricted role)
  listMinistryUsers: () => request("GET", "/ministry-users/"),
  createMinistryUser: (payload) => request("POST", "/ministry-users/", payload),
  deleteMinistryUser: (id) => request("DELETE", `/ministry-users/${id}/`),
  // exchange
  lookupPatient: (nid) => request("GET", `/patients/${nid}/`),
  patientIndex: (nid) => request("GET", `/patients/${nid}/index/`),
  fetchRecords: (nid, mode, recordIndexId) =>
    request("POST", `/patients/${nid}/fetch/`, {
      mode,
      record_index_id: recordIndexId,
    }),
  // patient portal
  activatePatient: (payload) =>
    request("POST", "/patient/activate/", payload, false),
  registerPatient: (payload) =>
    request("POST", "/patient/register/", payload, false),
  myRecords: () => request("GET", "/patient/records/"),
  myBundle: () => request("GET", "/patient/bundle/"),
  // announcements
  listAnnouncements: () => request("GET", "/announcements/"),
  createAnnouncement: (payload) => request("POST", "/announcements/", payload),
  deleteAnnouncement: (id) => request("DELETE", `/announcements/${id}/`),
  // audit & analytics
  audit: (filters) => {
    const qs = filters ? new URLSearchParams(filters).toString() : "";
    return request("GET", `/audit/${qs ? "?" + qs : ""}`);
  },
  // the signed-in user's own access history (doctor dashboard feed)
  myActivity: () => request("GET", "/me/activity/"),
  analytics: () => request("GET", "/analytics/summary/"),
  facilityAnalytics: () => request("GET", "/analytics/facility/"),
};
