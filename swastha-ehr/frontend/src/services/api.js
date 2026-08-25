import axios from "axios";

// Central axios instance. Auth is carried by httpOnly cookies (access_token /
// refresh_token) set by the backend on login — never by JavaScript-readable
// tokens — so an XSS payload cannot exfiltrate a session. The SPA is served
// same-origin with the API (the "/api" prefix is proxied to Django by Vite in
// dev and nginx in prod), so the SameSite=Lax cookies and the double-submit
// CSRF token work without CORS.
const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Only the non-sensitive user object is mirrored into localStorage, purely so a
// hard refresh can render the right screen before the first API call returns.
export const USER_KEY = "swasthya_user";

const UNSAFE_METHODS = new Set(["post", "put", "patch", "delete"]);

function getCookie(name) {
  const match = document.cookie.match(
    "(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)",
  );
  return match ? decodeURIComponent(match[1]) : null;
}

// Prime the csrftoken cookie once (a GET is CSRF-exempt) so the very first
// state-changing request after a cold load already has a token to echo.
let csrfPrimed = false;
export async function ensureCsrf() {
  if (csrfPrimed || getCookie("csrftoken")) {
    csrfPrimed = true;
    return;
  }
  try {
    await api.get("/v1/auth/csrf/");
  } catch {
    /* network error — the triggering request will surface it */
  }
  csrfPrimed = true;
}

// Before every state-changing request, echo the csrftoken cookie in the
// X-CSRFToken header (Django's double-submit check). GET/HEAD are exempt.
api.interceptors.request.use(async (config) => {
  if (UNSAFE_METHODS.has((config.method || "get").toLowerCase())) {
    await ensureCsrf();
    const csrf = getCookie("csrftoken");
    if (csrf) config.headers["X-CSRFToken"] = csrf;
  }
  return config;
});

// RESPONSE INTERCEPTOR: silent refresh on expiry
// ----------------------------------------------
// A separate instance WITHOUT interceptors calls the refresh endpoint, so a
// failed refresh cannot recurse back through this chain.
const refreshApi = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Auth endpoints must never trigger the refresh-on-401 retry (they issue or
// depend on the very cookies a refresh would rotate — retrying loops).
const NO_REFRESH = [
  "/v1/auth/login/",
  "/v1/auth/refresh/",
  "/v1/auth/logout/",
  "/v1/auth/csrf/",
];

api.interceptors.response.use(
  // If the request succeeds, just pass it through.
  (response) => response,

  // If the request fails:
  async (error) => {
    const originalRequest = error.config;
    const url = originalRequest?.url || "";

    // Only handle 401s, once, and never for the auth endpoints themselves.
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !NO_REFRESH.some((path) => url.includes(path))
    ) {
      originalRequest._retry = true;

      try {
        // Refresh reads the refresh_token cookie and rotates the access cookie;
        // no body needed. Send CSRF explicitly (the clean instance has no
        // interceptor to add it).
        const csrf = getCookie("csrftoken");
        await refreshApi.post("/v1/auth/refresh/", null, {
          headers: csrf ? { "X-CSRFToken": csrf } : {},
        });

        // Cookie rotated — just replay the original request.
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed — the refresh cookie is probably expired or invalid.
        // Drop the cached user and bounce to login.
        localStorage.removeItem(USER_KEY);

        // Avoid redirect loops: only redirect if not already on the login page.
        if (!window.location.pathname.includes("/login")) {
          window.location.href = "/login";
        }

        return Promise.reject(refreshError);
      }
    }

    // Not a 401, already retried, or an auth endpoint — just reject.
    return Promise.reject(error);
  },
);

export default api;
