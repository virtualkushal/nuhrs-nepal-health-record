import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { HeartPulse, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ROLE_HOME } from "../constants";

// Email + password login for every role.
export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(email.trim().toLowerCase(), password);
      // Force a password change on first login.
      if (user.must_change_password) {
        navigate("/change-password", { replace: true });
        return;
      }
      navigate(ROLE_HOME[user.role] || "/", { replace: true });
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center">
          <Link to="/" className="rounded-2xl bg-gradient-to-br from-brand-500 to-brand-800 p-3 shadow-lg shadow-brand-900/40">
            <HeartPulse className="h-7 w-7 text-white" />
          </Link>
          <h1 className="mt-3 font-display text-2xl font-bold text-white">
            Swasthya<span className="text-brand-400">EHR</span>
          </h1>
          <p className="text-sm text-gray-400">Sign in to your workspace</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-card space-y-4 rounded-2xl p-8">
          {error && <div className="alert-error">{error}</div>}
          <div>
            <label className="label">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="you@example.com"
              className="input"
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="input"
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Sign in
          </button>
          <div className="flex items-center justify-between text-sm">
            <Link to="/forgot-password" className="link">
              Forgot password?
            </Link>
            <Link to="/register" className="text-gray-400 hover:text-white">
              New patient? Register
            </Link>
          </div>
          <p className="text-center text-xs text-gray-500">
            Staff? <Link to="/staff-register" className="link">Request a staff account</Link>
          </p>
        </form>
      </div>
    </div>
  );

}
