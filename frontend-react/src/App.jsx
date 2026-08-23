import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import Landing from "./pages/Landing.jsx";
import RegisterOrg from "./pages/RegisterOrg.jsx";
import ActivatePatient from "./pages/ActivatePatient.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import SSOLogin from "./pages/SSOLogin.jsx";

export default function App() {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Public home. Redirect to the app if already signed in. */}
      <Route
        path="/"
        element={user ? <Navigate to="/app" replace /> : <Landing />}
      />
      <Route path="/register-org" element={<RegisterOrg />} />
      <Route path="/activate" element={<ActivatePatient />} />
      {/* Seamless handoff target for doctors arriving from SwasthyaEHR. */}
      <Route path="/sso-login" element={<SSOLogin />} />

      <Route path="/app" element={<Dashboard />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
