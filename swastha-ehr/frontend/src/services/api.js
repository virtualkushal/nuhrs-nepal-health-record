import axios from "axios";

// Central axios instance. All API calls go through here so we have a single
// place to attach the JWT token and base URL. The "/api" prefix is proxied to
// the Django backend by Vite during development.
const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Where we keep the access token in the browser. (localStorage is fine for a
// student project; a production app would prefer httpOnly cookies.)
export const TOKEN_KEY = "swasthya_access";
export const REFRESH_KEY = "swasthya_refresh";
export const USER_KEY = "swasthya_user";

// Before every request, attach the token if we have one.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

//RESPONSE INTERCEPTOR: Handle expired tokens
// ----------------------------------------------
// We need a separate axios instance WITHOUT interceptors to call the refresh
// endpoint, otherwise we'd get an infinite loop if the refresh itself fails.
const refreshApi = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  // If the request succeeds, just pass it through.
  (response) => response,

  // If the request fails:
  async (error) => {
    const originalRequest = error.config;

    // Only handle 401 errors, and only if we haven't already tried to refresh.
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem(REFRESH_KEY);
        if (!refreshToken) {
          throw new Error("No refresh token available");
        }

        // Call the refresh endpoint using the clean axios instance
        const res = await refreshApi.post("/v1/auth/refresh/", {
          refresh: refreshToken,
        });

        const newAccessToken = res.data.access;
        localStorage.setItem(TOKEN_KEY, newAccessToken);

        // Update the Authorization header on the original request and retry it
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed — the refresh token is probably expired or invalid.
        // Clean up and redirect to login.
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
        localStorage.removeItem(USER_KEY);

        // Avoid redirect loops: only redirect if we're not already on the login page.
        if (!window.location.pathname.includes("/login")) {
          window.location.href = "/login";
        }

        return Promise.reject(refreshError);
      }
    }

    // If it's not a 401, or we already tried to refresh, just reject.
    return Promise.reject(error);
  }
);

export default api;
