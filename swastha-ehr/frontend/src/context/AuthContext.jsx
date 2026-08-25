import { createContext, useContext, useEffect, useState } from "react";
import api, { USER_KEY, ensureCsrf } from "../services/api";

// Global authentication state: who is logged in, their role, and login/logout
// helpers. Login is by EMAIL in v2. Any component reads this via useAuth().
//
// Auth tokens live in httpOnly cookies set by the backend; this context only
// tracks the non-sensitive user object (mirrored to localStorage so a hard
// refresh renders the right screen before the first API call returns).
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Prime the CSRF cookie early so the first write has a token to echo.
    ensureCsrf();
    const stored = localStorage.getItem(USER_KEY);
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem(USER_KEY);
      }
    }
    setLoading(false);
  }, []);

  async function login(email, password) {
    // On success the backend sets the httpOnly JWT cookies and returns { user }.
    const res = await api.post("/v1/auth/login/", { email, password });
    const userData = res.data.user;
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
    setUser(userData);
    return userData;
  }

  // After a forced password change, clear the flag locally.
  function clearMustChangePassword() {
    setUser((prev) => {
      if (!prev) return prev;
      const next = { ...prev, must_change_password: false };
      localStorage.setItem(USER_KEY, JSON.stringify(next));
      return next;
    });
  }

  async function logout() {
    // Best-effort server-side cookie clear; local state is dropped regardless so
    // a network hiccup can never strand the user in a logged-in-looking shell.
    try {
      await api.post("/v1/auth/logout/");
    } catch {
      /* ignore — clearing local state below is what matters */
    }
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, logout, clearMustChangePassword }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
