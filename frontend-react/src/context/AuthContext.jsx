import { createContext, useContext, useState, useCallback } from "react";
import { api, currentUser, saveUser, clearSession } from "../lib/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => currentUser());

  // Accepts a credentials object, e.g.
  //   { scope: "STAFF", org_code, login_name, password }
  //   { scope: "PATIENT", username, password }
  //   { scope: "OFFICIAL", username, password }   (Super Admin or Ministry)
  const login = useCallback(async (credentials) => {
    const data = await api.login(credentials);
    // Tokens now live in httpOnly cookies set by the server; we persist only the
    // non-sensitive user object so a hard refresh can render the right dashboard.
    saveUser(data.user);
    setUser(data.user);
    return data.user;
  }, []);

  // Adopt a session that was obtained without a password prompt — currently the
  // SwasthyaEHR single sign-on handoff, which redeems a ticket. The cookies are
  // set on the sso-verify response; we only mirror the returned user. Doing this
  // in-context (rather than writing localStorage and reloading the page) keeps it
  // to a single document load, so in-flight font/asset requests are not cancelled
  // by a second navigation.
  const adoptSession = useCallback((data) => {
    saveUser(data.user);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    // Best-effort server-side cookie clear; local state is dropped regardless so
    // a network hiccup can never strand the user in a logged-in-looking shell.
    try {
      await api.logout();
    } catch {
      /* ignore — clearing local state below is what matters */
    }
    clearSession();
    setUser(null);
  }, []);

  const completePasswordChange = useCallback(() => {
    setUser((prev) => {
      if (!prev) return prev;
      const next = { ...prev, must_change_password: false };
      saveUser(next);
      return next;
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, login, adoptSession, logout, completePasswordChange }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
