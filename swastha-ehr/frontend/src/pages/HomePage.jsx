import { useEffect, useState } from "react";
import { Activity, CheckCircle2, XCircle, Loader2, LogOut } from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

// Shared landing page. Confirms the backend connection and shows who is signed
// in. Roles without a dedicated dashboard yet (doctor, lab tech, pharmacist)
// land here until their screens are built in later parts.
export default function HomePage() {
  const { user, logout } = useAuth();
  const [state, setState] = useState({ status: "loading", data: null });

  useEffect(() => {
    api
      .get("/v1/health/")
      .then((res) => setState({ status: "ok", data: res.data }))
      .catch(() => setState({ status: "error", data: null }));
  }, []);

  return (
    <div className="min-h-screen bg-surface-800 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-surface-750 rounded-2xl shadow-sm border border-line p-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-brand-500/20 rounded-lg">
              <Activity className="w-6 h-6 text-brand-300" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">SwasthyaEHR</h1>
              <p className="text-sm text-gray-400">
                Hospital EHR &amp; Pharmacy Safety System
              </p>
            </div>
          </div>
          {user && (
            <button
              onClick={logout}
              className="flex items-center gap-1 text-sm text-gray-400 hover:text-white"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>

        {user && (
          <div className="mb-4 rounded-lg border border-line bg-surface-700 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500 mb-1">
              Signed in
            </p>
            <p className="text-white">
              {user.full_name}{" "}
              <span className="text-gray-500">({user.role})</span>
            </p>
            <p className="text-xs text-gray-500 mt-1">
              A dashboard for this role will arrive in a later part.
            </p>
          </div>
        )}

        <div className="rounded-lg border border-line bg-surface-700 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500 mb-2">
            Backend connection
          </p>

          {state.status === "loading" && (
            <div className="flex items-center gap-2 text-gray-300">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Checking connection to the API…</span>
            </div>
          )}

          {state.status === "ok" && (
            <div className="flex items-center gap-2 text-brand-300">
              <CheckCircle2 className="w-5 h-5" />
              <span>Connected — API reports “{state.data.status}”</span>
            </div>
          )}

          {state.status === "error" && (
            <div className="flex items-center gap-2 text-red-300">
              <XCircle className="w-5 h-5" />
              <span>Could not reach the backend. Is the Django server running?</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
