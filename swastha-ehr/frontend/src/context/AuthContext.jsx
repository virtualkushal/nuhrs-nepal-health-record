import { createContext, useContext, useEffect, useState } from "react";
import api, { TOKEN_KEY, REFRESH_KEY, USER_KEY } from "../services/api";

// Global authentication state: who is logged in, their role, and login/logout
// helpers. Login is by EMAIL in v2. Any component reads this via useAuth().
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
    const res = await api.post("/v1/auth/login/", { email, password });
    const { access, refresh, user: userData } = res.data;
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
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

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
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
