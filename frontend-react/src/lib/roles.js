// Single source of truth for where each role "lives" in the URL space.
//
// The login form, the SwasthyaEHR SSO handoff, the `/` redirect and
// ProtectedRoute all read from this map, so they can never disagree about which
// dashboard a given user belongs to.

export const LOGIN_PATH = "/login";

export const ROLE_HOME = {
  SUPER_ADMIN: "/ministry",
  ORGANIZATION_ADMIN: "/org-admin",
  DOCTOR: "/doctor",
  LAB_TECHNICIAN: "/exchange",
  PATIENT: "/patient",
};

// Resolve the dashboard path for a user object from AuthContext.
// - no user            -> the sign-in page
// - unrecognised role  -> the "no access" screen (rather than a redirect loop)
export function dashboardPathFor(user) {
  if (!user) return LOGIN_PATH;
  return ROLE_HOME[user.role] || "/unauthorized";
}
