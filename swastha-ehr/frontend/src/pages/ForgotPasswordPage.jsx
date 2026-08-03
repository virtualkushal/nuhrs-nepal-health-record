import { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, Loader2, CheckCircle2 } from "lucide-react";
import api from "../services/api";
import BrandMark from "../components/BrandMark";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      await api.post("/v1/auth/password-reset/", { email });
      setSuccess(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-800 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-surface-750 rounded-2xl shadow-sm border border-line p-8">
        <BrandMark subtitle="Reset your password" />

        {success ? (
          <div className="mt-6 text-center">
            <CheckCircle2 className="mx-auto h-12 w-12 text-brand-400 mb-3" />
            <h2 className="text-lg font-semibold text-white">Check your email</h2>
            <p className="text-sm text-gray-300 mt-2">
              If an account exists with <strong>{email}</strong>, you'll receive
              a password reset link shortly.
            </p>
            <Link
              to="/login"
              className="mt-6 inline-block text-sm text-brand-300 hover:underline"
            >
              Back to login
            </Link>
          </div>
        ) : (
          <>
            <p className="mt-2 text-sm text-gray-400">
              Enter the email address you used to sign up, and we'll send you a
              link to reset your password.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-1">
                  Email address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full rounded-lg border border-line pl-10 pr-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="you@hospital.org.np"
                  />
                </div>
              </div>

              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm px-3 py-2">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-60 text-white font-medium rounded-lg px-4 py-2.5"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : null}
                {loading ? "Sending..." : "Send reset link"}
              </button>

              <p className="text-center text-sm text-gray-400">
                Remember your password?{" "}
                <Link to="/login" className="text-brand-300 hover:underline">
                  Sign in
                </Link>
              </p>
            </form>
          </>
        )}
      </div>
    </div>
  );
}