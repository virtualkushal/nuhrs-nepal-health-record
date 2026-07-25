// Thin fetch wrapper around the National Platform API with JWT handling.
const API = (() => {
  const base = window.NUHRS_CONFIG.PLATFORM_API;

  function token() {
    return window.localStorage.getItem("nuhrs_access");
  }

  function setSession(data) {
    window.localStorage.setItem("nuhrs_access", data.access);
    window.localStorage.setItem("nuhrs_refresh", data.refresh);
    window.localStorage.setItem("nuhrs_user", JSON.stringify(data.user));
  }

  function currentUser() {
    const raw = window.localStorage.getItem("nuhrs_user");
    return raw ? JSON.parse(raw) : null;
  }

  function clear() {
    ["nuhrs_access", "nuhrs_refresh", "nuhrs_user"].forEach((k) =>
      window.localStorage.removeItem(k)
    );
  }

  async function request(method, path, body, auth = true) {
    const headers = { "Content-Type": "application/json" };
    if (auth && token()) headers["Authorization"] = `Bearer ${token()}`;
    const res = await fetch(base + path, {
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

  return {
    setSession,
    currentUser,
    clear,
    token,
    // auth
    login: (username, password) =>
      request("POST", "/auth/login/", { username, password }, false),
    changePassword: (new_password) =>
      request("POST", "/auth/change-password/", { new_password }),
    // organizations
    registerOrg: (payload) =>
      request("POST", "/orgs/register/", payload, false),
    listOrgs: (status) =>
      request("GET", `/orgs/${status ? "?status=" + status : ""}`),
    approveOrg: (id) => request("POST", `/orgs/${id}/approve/`),
    rejectOrg: (id) => request("POST", `/orgs/${id}/reject/`),
    // staff
    listStaff: () => request("GET", "/staff/"),
    createStaff: (payload) => request("POST", "/staff/", payload),
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
    myRecords: () => request("GET", "/patient/records/"),
    // audit & analytics
    audit: (nid) => request("GET", `/audit/${nid ? "?nid=" + nid : ""}`),
    analytics: () => request("GET", "/analytics/summary/"),
  };
})();
