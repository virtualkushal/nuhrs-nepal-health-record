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

  const login = useCallback(async (username, password) => {
    const data = await api.login(username, password);
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
