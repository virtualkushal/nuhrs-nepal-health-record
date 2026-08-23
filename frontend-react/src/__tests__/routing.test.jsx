import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../context/AuthContext.jsx";
import { ToastProvider } from "../context/ToastContext.jsx";
import ProtectedRoute from "../components/ProtectedRoute.jsx";
import { ROLE_HOME, dashboardPathFor } from "../lib/roles.js";

// Stand-ins for the real dashboards: this suite exercises the routing guard,
// not the portals themselves.
function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<div>sign in page</div>} />
            <Route path="/unauthorized" element={<div>no access</div>} />
            <Route element={<ProtectedRoute allowedRoles={["DOCTOR"]} />}>
              <Route path="/doctor/*" element={<div>doctor portal</div>} />
            </Route>
            <Route element={<ProtectedRoute allowedRoles={["PATIENT"]} />}>
              <Route path="/patient/*" element={<div>patient portal</div>} />
            </Route>
            <Route element={<ProtectedRoute allowedRoles={["SUPER_ADMIN"]} />}>
              <Route path="/ministry/*" element={<div>ministry portal</div>} />
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

function signIn(user) {
  window.localStorage.setItem("nuhrs_access", "fake-access-token");
  window.localStorage.setItem("nuhrs_refresh", "fake-refresh-token");
  window.localStorage.setItem("nuhrs_user", JSON.stringify(user));
}

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(cleanup);

describe("dashboardPathFor", () => {
  it("maps every supported role to its own URL prefix", () => {
    expect(dashboardPathFor({ role: "SUPER_ADMIN" })).toBe("/ministry");
    expect(dashboardPathFor({ role: "ORGANIZATION_ADMIN" })).toBe("/org-admin");
    expect(dashboardPathFor({ role: "DOCTOR" })).toBe("/doctor");
    expect(dashboardPathFor({ role: "PATIENT" })).toBe("/patient");
    expect(dashboardPathFor({ role: "LAB_TECHNICIAN" })).toBe("/exchange");
    expect(Object.keys(ROLE_HOME)).toHaveLength(5);
  });

  it("sends anonymous visitors to /login and unknown roles to /unauthorized", () => {
    expect(dashboardPathFor(null)).toBe("/login");
    expect(dashboardPathFor({ role: "SOMETHING_NEW" })).toBe("/unauthorized");
  });
});

describe("ProtectedRoute", () => {
  it("redirects an anonymous visitor to the sign-in page", () => {
    renderAt("/doctor");
    expect(screen.getByText("sign in page")).toBeTruthy();
  });

  it("renders the portal when the role matches the route", () => {
    signIn({ role: "DOCTOR", username: "doctor", full_name: "Dr. Sharma" });
    renderAt("/doctor");
    expect(screen.getByText("doctor portal")).toBeTruthy();
  });

  it("keeps the user on their own route after a hard refresh (session read from localStorage)", () => {
    // Nothing but localStorage is populated here — exactly the state a browser
    // reload of /patient starts from.
    signIn({ role: "PATIENT", username: "12345678901" });
    renderAt("/patient");
    expect(screen.getByText("patient portal")).toBeTruthy();
    expect(screen.queryByText("sign in page")).toBeNull();
  });

  it("bounces a signed-in user off another role's route to their own dashboard", () => {
    signIn({ role: "PATIENT", username: "12345678901" });
    renderAt("/doctor");
    expect(screen.getByText("patient portal")).toBeTruthy();
    expect(screen.queryByText("doctor portal")).toBeNull();
  });

  it("supports deep links inside a portal", () => {
    signIn({ role: "SUPER_ADMIN", username: "superadmin" });
    renderAt("/ministry/organizations");
    expect(screen.getByText("ministry portal")).toBeTruthy();
  });

  it("forces a password change before any dashboard is reachable", () => {
    signIn({ role: "DOCTOR", username: "doctor", must_change_password: true });
    renderAt("/doctor");
    expect(screen.getByText("Set a new password")).toBeTruthy();
    expect(screen.queryByText("doctor portal")).toBeNull();
  });
});
