import { createContext, useContext, useState, useCallback } from "react";
import {
  api,
  setSession,
  currentUser,
  saveUser,
  clearSession,
} from "../lib/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => currentUser());

  // Accepts a credentials object, e.g.
  //   { scope: "STAFF", org_code, login_name, password }
  //   { scope: "PATIENT", username, password }
  //   { scope: "MINISTRY", username, password }
  const login = useCallback(async (credentials) => {
    const data = await api.login(credentials);
    setSession(data);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
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
      value={{ user, login, logout, completePasswordChange }}
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
