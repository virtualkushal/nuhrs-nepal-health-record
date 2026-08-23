import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../lib/api.js";
import { dashboardPathFor } from "../lib/roles.js";

// Landing page for the seamless SwasthyaEHR -> NUHRS handoff.
//
// SwasthyaEHR's backend already proved its identity to the National Platform
// and obtained a single-use ticket; the doctor's browser arrives here as
// /sso-login?ticket=...&nid=... . We redeem the ticket for JWT tokens, adopt the
// session in the auth context, and route to that user's role dashboard (usually
// /doctor) — all within this single document load, so the icon font and JS
// bundle are never re-fetched.
export default function SSOLogin() {
  const [params] = useSearchParams();
  const { adoptSession } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  // Tickets are single-use: guard against React StrictMode's double effect,
  // which would burn the ticket on the first call and fail on the second.
  const redeemed = useRef(false);

  useEffect(() => {
    if (redeemed.current) return;
    redeemed.current = true;

    const ticket = params.get("ticket");
    const nid = params.get("nid");

    if (!ticket) {
      setError("No single sign-on ticket was provided.");
      return;
    }

    api
      .ssoVerify(ticket)
      .then((data) => {
        // Pass the patient context (if any) to the doctor dashboard.
        if (nid) window.sessionStorage.setItem("nuhrs_sso_nid", nid);
        else window.sessionStorage.removeItem("nuhrs_sso_nid");
        const signedIn = adoptSession(data);
        navigate(dashboardPathFor(signedIn), { replace: true });
      })

      .catch((err) => {
        setError(
          err?.message ||
            "This single sign-on link is no longer valid. Please try again from SwasthyaEHR.",
        );
      });
  }, [params]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-md rounded-2xl border border-red-200 bg-white p-8 text-center shadow-sm">
          <span className="material-symbols-outlined text-[40px] text-red-600">
            link_off
          </span>
          <h1 className="mt-2 text-lg font-semibold text-slate-900">
            SSO session expired or invalid
          </h1>
          <p className="mt-2 text-sm text-slate-600">{error}</p>
          <p className="mt-2 text-xs text-slate-500">
            Single sign-on links can only be used once and expire after one
            minute. Return to SwasthyaEHR and click National Dashboard again.
          </p>
          <Link
            to="/"
            className="mt-6 inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          >
            Go to NUHRS sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex min-h-screen items-center justify-center p-6"
      role="status"
      aria-live="polite"
    >
      <div className="text-center">
        <span className="material-symbols-outlined animate-spin text-[40px] text-teal-700">
          progress_activity
        </span>
        <h1 className="mt-3 text-lg font-semibold text-slate-900">
          Signing you in to NUHRS…
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Verifying your SwasthyaEHR session with the National Platform.
        </p>
      </div>
    </div>
  );
}
