import { Archive, Building2, HeartPulse, Inbox, LogOut } from "lucide-react";
import { Link } from "react-router-dom";
import { ROLE_THEME, DEFAULT_THEME } from "../constants";


// Shared top bar for every role dashboard. Picks up a per-role color theme
// (gradient brand tile + role badge) so each workspace feels distinct while
// staying consistent. `subtitle` overrides the theme's default workspace label.
export default function DashboardHeader({ user, logout, subtitle }) {
  const theme = ROLE_THEME[user?.role] || DEFAULT_THEME;
  const initials = (user?.full_name || "?")
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="sticky top-0 z-40 border-b border-outline-variant bg-surface/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <div
            className={`rounded-xl bg-gradient-to-br ${theme.gradient} p-2 shadow-lg shadow-black/10`}
          >
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
            <>
              <Link
                to="/doctor/cross-hospital"
                className="hidden items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface sm:flex"
              >
                <Building2 className="h-4 w-4" /> Cross-Hospital
              </Link>
              <Link
                to="/doctor/imported-records"
                className="hidden items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface sm:flex"
              >
                <Archive className="h-4 w-4" /> Imported Records
              </Link>
            </>
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
            <div
              className={`flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br ${theme.gradient} text-xs font-semibold text-white`}
            >
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