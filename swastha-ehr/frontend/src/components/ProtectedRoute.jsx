import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Guards a route. If no one is logged in, send them to /login. If `roles` is
// given and the user's role isn't in it, send them to their own home.
export default function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();

  if (loading) return null; // brief flash while we read localStorage

  if (!user) return <Navigate to="/login" replace />;

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
}
