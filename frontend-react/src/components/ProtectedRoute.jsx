import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import AppShell from "./AppShell.jsx";
import ChangePassword from "../pages/ChangePassword.jsx";
import { dashboardPathFor, LOGIN_PATH } from "../lib/roles.js";

// Route guard for the authenticated area.
//
// Usage — either as a layout route wrapping child routes:
//   <Route element={<ProtectedRoute allowedRoles={["DOCTOR"]} />}>
//     <Route path="/doctor/*" element={<DoctorPortal />} />
//   </Route>
// or directly around a single element:
//   <ProtectedRoute allowedRoles={["PATIENT"]}><PatientPortal /></ProtectedRoute>
//
// Session state comes from AuthContext, which seeds itself synchronously from
// localStorage. There is therefore no async "still loading" window on a hard
// refresh, so /doctor or /patient survive F5 without bouncing through /login.
export default function ProtectedRoute({ allowedRoles, children }) {
  const { user } = useAuth();
  const location = useLocation();

  // Not signed in: send them to sign in, remembering where they were headed so
  // the login handler can return them there afterwards.
  if (!user) {
    return <Navigate to={LOGIN_PATH} state={{ from: location }} replace />;
  }

  // Accounts issued a temporary password must replace it before any dashboard
  // becomes reachable (previously handled inside Dashboard.jsx).
  if (user.must_change_password) return <ChangePassword />;

  const home = dashboardPathFor(user);

  // Signed in, but this route belongs to a different role: hand them their own
  // dashboard instead. If that is where they already are (or the role has no
  // dashboard at all), fall back to the explicit "no access" screen so we never
  // redirect in a loop.
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    const target = home === location.pathname ? "/unauthorized" : home;
    return <Navigate to={target} replace />;
  }

  return <AppShell>{children ?? <Outlet />}</AppShell>;
}
