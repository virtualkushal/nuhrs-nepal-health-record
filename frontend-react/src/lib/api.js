// Thin fetch wrapper around the National Platform API with JWT handling.
// Modular ES-module version of the original api.js.

const API_BASE =
  (window.localStorage.getItem("nuhrs_api") ||
    import.meta.env.VITE_PLATFORM_API ||
    "http://localhost:8000") + "/api";

export function token() {
  return window.localStorage.getItem("nuhrs_access");
}

export function setSession(data) {
  window.localStorage.setItem("nuhrs_access", data.access);
  window.localStorage.setItem("nuhrs_refresh", data.refresh);
  window.localStorage.setItem("nuhrs_user", JSON.stringify(data.user));
}

export function currentUser() {
  const raw = window.localStorage.getItem("nuhrs_user");
  return raw ? JSON.parse(raw) : null;
}

export function saveUser(user) {
  window.localStorage.setItem("nuhrs_user", JSON.stringify(user));
}

export function clearSession() {
  ["nuhrs_access", "nuhrs_refresh", "nuhrs_user"].forEach((k) =>
    window.localStorage.removeItem(k),
  );
}

async function request(method, path, body, auth = true) {
  const headers = { "Content-Type": "application/json" };
  if (auth && token()) headers["Authorization"] = `Bearer ${token()}`;
  const res = await fetch(API_BASE + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) {
    const err = new Error(data.detail || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  // auth
  // Accepts a credentials object. Supported shapes:
  //   Staff:    { scope: "STAFF",    org_code, login_name, password }
  //   Patient:  { scope: "PATIENT",  username, password }   (username = NID)
  //   Official: { scope: "OFFICIAL", username, password }   (Super Admin or Ministry)
  // A bare { username, password } (no scope) still works (legacy path).
  login: (credentials) => request("POST", "/auth/login/", credentials, false),
  // Redeem a single-use SSO ticket issued to a trusted facility (e.g. a doctor
  // arriving from SwasthyaEHR) for standard JWT tokens.
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
