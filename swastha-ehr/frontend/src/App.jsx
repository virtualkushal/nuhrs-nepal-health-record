import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import StaffRegisterPage from "./pages/StaffRegisterPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import AdminDashboard from "./pages/AdminDashboard";
import ReceptionDashboard from "./pages/ReceptionDashboard";
import NurseDashboard from "./pages/NurseDashboard";
import DoctorDashboard from "./pages/DoctorDashboard";
import PharmacyDashboard from "./pages/PharmacyDashboard";
import LabDashboard from "./pages/LabDashboard";
import PatientPortal from "./pages/PatientPortal";
import HospitalBViewer from "./pages/HospitalBViewer";
import CrossHospital from "./pages/CrossHospital";
import ImportedRecords from "./pages/ImportedRecords";
import AdminShareApprovals from "./pages/AdminShareApprovals";


// App routing.
// Public: landing, login, patient register, staff register, password flows,
// and the standalone Hospital B viewer (interoperability demo).
// Protected + role-gated: one dashboard per role.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/staff-register" element={<StaffRegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:uid/:token/" element={<ResetPasswordPage />} />
      <Route path="/hospital-b" element={<HospitalBViewer />} />

      <Route
        path="/change-password"
        element={
          <ProtectedRoute>
            <ChangePasswordPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute roles={["ADMIN"]}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reception"
        element={
          <ProtectedRoute roles={["RECEPTIONIST"]}>
            <ReceptionDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/nurse"
        element={
          <ProtectedRoute roles={["NURSE"]}>
            <NurseDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/doctor"
        element={
          <ProtectedRoute roles={["DOCTOR"]}>
            <DoctorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/doctor/cross-hospital"
        element={
          <ProtectedRoute roles={["DOCTOR"]}>
            <CrossHospital />
          </ProtectedRoute>
        }
      />
      <Route
        path="/doctor/imported-records"
        element={
          <ProtectedRoute roles={["DOCTOR"]}>
            <ImportedRecords />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/share-requests"
        element={
          <ProtectedRoute roles={["ADMIN"]}>
            <AdminShareApprovals />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pharmacy"

        element={
          <ProtectedRoute roles={["PHARMACIST"]}>
            <PharmacyDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/lab"
        element={
          <ProtectedRoute roles={["LAB_TECH"]}>
            <LabDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/portal"
        element={
          <ProtectedRoute roles={["PATIENT"]}>
            <PatientPortal />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
