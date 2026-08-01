import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import AppShell from "../components/AppShell.jsx";
import ChangePassword from "./ChangePassword.jsx";
import SuperAdmin from "./dashboards/SuperAdmin.jsx";
import OrgAdmin from "./dashboards/OrgAdmin.jsx";
import Exchange from "./dashboards/Exchange.jsx";
import DoctorPortal from "./dashboards/DoctorPortal.jsx";
import PatientPortal from "./dashboards/PatientPortal.jsx";

// Authenticated area: picks the right dashboard based on the user's role.
export default function Dashboard() {
  const { user } = useAuth();

  if (!user) return <Navigate to="/" replace />;
  if (user.must_change_password) return <ChangePassword />;

  let body;
  switch (user.role) {
    case "SUPER_ADMIN":
      body = <SuperAdmin />;
      break;
    case "ORGANIZATION_ADMIN":
      body = <OrgAdmin />;
      break;
    case "DOCTOR":
      body = <DoctorPortal />;
      break;
    case "LAB_TECHNICIAN":
      body = <Exchange />;
      break;
    case "PATIENT":
      body = <PatientPortal />;
      break;
    default:
      return <Navigate to="/" replace />;
  }

  return <AppShell>{body}</AppShell>;
}
