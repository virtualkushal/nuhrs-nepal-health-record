import { Globe, HeartPulse, Inbox, Loader2, LogOut } from "lucide-react";

import { useState } from "react";
import { Link } from "react-router-dom";
import { ROLE_THEME, DEFAULT_THEME } from "../constants";
import api from "../services/api";

// Shared top bar for every role dashboard. Brand tile is flat NUHRS teal for
// all roles; the per-role accent lives in the small role badge and ring.
// `subtitle` overrides the theme's default workspace label.
export default function DashboardHeader({ user, logout, subtitle }) {
  const theme = ROLE_THEME[user?.role] || DEFAULT_THEME;
  const [launching, setLaunching] = useState(false);
  const initials = (user?.full_name || "?")
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  // Seamless SSO handoff to the NUHRS National Dashboard. The backend exchanges
  // this facility's API key for a single-use ticket and returns a one-shot URL
  // we open in a new tab — the doctor lands logged in, no second sign-in.
  const launchNationalDashboard = async () => {
    if (launching) return;
    setLaunching(true);
    try {
      const { data } = await api.get("/v1/nuhrs/launch/");
      if (data?.sso_url) {
        // noopener keeps the new tab from touching this window; we deliberately
        // do NOT add noreferrer, which would force a no-referrer policy on the
        // portal document and its font/asset requests.
        window.open(data.sso_url, "_blank", "noopener");
      } else {
        alert("Could not open the National Dashboard. Please try again.");
      }
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        "Could not reach the NUHRS National Platform. Please try again.";
      alert(detail);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 border-b border-outline-variant bg-surface/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary p-2 shadow-sm">
            <HeartPulse className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="font-display font-bold tracking-tight text-on-surface">
              Swasthya<span className="text-primary">EHR</span>
            </h1>
            <p className="text-xs text-on-surface-variant">
              {subtitle || theme.label}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {user?.role === "DOCTOR" && (
            <button
              type="button"
              onClick={launchNationalDashboard}
              disabled={launching}
              title="Open the NUHRS National Dashboard (single sign-on)"
              className="hidden items-center gap-1.5 rounded-lg bg-primary px-2.5 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60 sm:flex"
            >
              {launching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Globe className="h-4 w-4" />
              )}
              {launching ? "Opening…" : "National Dashboard"}
            </button>
          )}

          {user?.role === "ADMIN" && (
            <Link
              to="/admin/share-requests"
              className="hidden items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface sm:flex"
            >
              <Inbox className="h-4 w-4" /> Incoming Requests
            </Link>
          )}
          <span
            className={`hidden rounded-full px-2.5 py-1 text-xs font-semibold sm:inline-block ${theme.badge}`}
          >
            {user?.role}
          </span>

          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-xs font-semibold text-white">
              {initials}
            </div>
            <span className="hidden text-sm text-on-surface-variant md:inline">
              {user?.full_name}
            </span>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm text-on-surface-variant transition-colors hover:bg-surface-container-low hover:text-on-surface"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Sign out</span>
          </button>
        </div>
      </div>
    </header>
  );
}
