import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { dashboardPathFor } from "../lib/roles.js";

// Shown when a signed-in account reaches a route its role cannot use, or when
// the role has no dashboard mapped at all.
export default function Unauthorized() {
  const { user, logout } = useAuth();
  const home = dashboardPathFor(user);

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl border border-outline-variant bg-surface-container-lowest p-8 text-center shadow-sm">
        <span className="material-symbols-outlined text-[40px] text-primary">
          lock
        </span>
        <h1 className="mt-2 font-title-lg text-title-lg text-on-surface">
          You don't have access to this area
        </h1>
        <p className="mt-2 text-body-md text-on-surface-variant">
          {user
            ? `Your account (${user.role}) is not permitted to view this page.`
            : "Please sign in to continue."}
        </p>
        <div className="mt-6 flex flex-col gap-3">
          <Link
            to={home}
            className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-label-md font-semibold text-on-primary hover:opacity-90"
          >
            {user ? "Go to my dashboard" : "Go to sign in"}
          </Link>
          {user && (
            <button onClick={logout} className="btn-ghost">
              Sign out
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
