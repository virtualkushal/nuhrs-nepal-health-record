import { useAuth } from "../context/AuthContext.jsx";
import Brand from "./Brand.jsx";


// Chrome for authenticated screens: top bar with brand, identity, and logout.
export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-outline-variant">
        <div className="h-16 max-w-container-max mx-auto px-margin-desktop flex items-center justify-between">
          <Brand size={28} subtitle />

          {user && (
            <div className="flex items-center gap-stack-md">
              <span className="text-label-md text-on-surface-variant">
                {(user.full_name || user.username) + " · " + user.role}
              </span>
              <button onClick={logout} className="btn-ghost">
                Logout
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="max-w-container-max mx-auto px-margin-desktop py-stack-xl">
        {children}
      </main>
    </div>
  );
}
