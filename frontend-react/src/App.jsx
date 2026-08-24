import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import { dashboardPathFor } from "./lib/roles.js";
import Landing from "./pages/Landing.jsx";
import RegisterOrg from "./pages/RegisterOrg.jsx";
import ActivatePatient from "./pages/ActivatePatient.jsx";
import SSOLogin from "./pages/SSOLogin.jsx";
import Unauthorized from "./pages/Unauthorized.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import SuperAdmin from "./pages/dashboards/SuperAdmin.jsx";
import Ministry from "./pages/dashboards/Ministry.jsx";
import OrgAdmin from "./pages/dashboards/OrgAdmin.jsx";
import Exchange from "./pages/dashboards/Exchange.jsx";
import DoctorPortal from "./pages/dashboards/DoctorPortal.jsx";
import PatientPortal from "./pages/dashboards/PatientPortal.jsx";

export default function App() {
  const { user } = useAuth();
  // Where this visitor belongs: their role dashboard, or /login when anonymous.
  const home = dashboardPathFor(user);

  return (
    <Routes>
      {/* ------------------------------------------------------------ public */}
      {/* Marketing home doubles as the sign-in page. Signed-in visitors are
          forwarded to their own dashboard instead. */}
      <Route
        path="/"
        element={user ? <Navigate to={home} replace /> : <Landing />}
      />
      <Route
        path="/login"
        element={user ? <Navigate to={home} replace /> : <Landing />}
      />
      <Route path="/register-org" element={<RegisterOrg />} />
      <Route path="/activate" element={<ActivatePatient />} />
      {/* Alias so /activate-patient links keep working. */}
      <Route
        path="/activate-patient"
        element={<Navigate to="/activate" replace />}
      />
      {/* Seamless handoff target for doctors arriving from SwasthyaEHR. */}
      <Route path="/sso-login" element={<SSOLogin />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      {/* -------------------------------------------- role-gated dashboards */}
      {/* Each portal gets its own bookmarkable prefix. The trailing splat keeps
          deeper links (e.g. /doctor/patients/123) inside that portal rather than
          falling through to the catch-all. */}
      <Route element={<ProtectedRoute allowedRoles={["SUPER_ADMIN"]} />}>
        <Route path="/admin/*" element={<SuperAdmin />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["MINISTRY"]} />}>
        <Route path="/ministry/*" element={<Ministry />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["ORGANIZATION_ADMIN"]} />}>
        <Route path="/org-admin/*" element={<OrgAdmin />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["DOCTOR"]} />}>
        <Route path="/doctor/*" element={<DoctorPortal />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["PATIENT"]} />}>
        <Route path="/patient/*" element={<PatientPortal />} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={["LAB_TECHNICIAN"]} />}>
        <Route path="/exchange/*" element={<Exchange />} />
      </Route>

      {/* ------------------------------------------------------------ legacy */}
      {/* The old single-view URL now just forwards to the caller's dashboard so
          existing bookmarks and any stale links still land somewhere useful. */}
      <Route path="/app" element={<Dashboard />} />
      <Route path="*" element={<Navigate to={user ? home : "/"} replace />} />
    </Routes>
  );
}
