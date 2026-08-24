import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { dashboardPathFor } from "../lib/roles.js";

// Legacy `/app` entry point.
//
// Role-based view switching now lives in the router: each role has its own
// bookmarkable prefix (/admin, /ministry, /org-admin, /doctor, /patient, /exchange)
// guarded by ProtectedRoute. This component only exists so old `/app` links
// forward to the right place — anonymous visitors land on /login.
export default function Dashboard() {
  const { user } = useAuth();
  return <Navigate to={dashboardPathFor(user)} replace />;
}
