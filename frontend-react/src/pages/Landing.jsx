import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { api } from "../lib/api.js";
import { dashboardPathFor } from "../lib/roles.js";
import Brand from "../components/Brand.jsx";
import background from "../assects/background.jpg";

// Public home page — Stitch "NUHRS Health Portal" design with a working login card.
export default function Landing() {
  const { login } = useAuth();
  const { show } = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  // Login tab: PATIENT | DOCTOR | MINISTRY
  const [tab, setTab] = useState("PATIENT");
  // Patient sub-mode: SIGNIN | REGISTER
  const [patientMode, setPatientMode] = useState("SIGNIN");

  // DOCTOR fields
  const [hospitals, setHospitals] = useState([]);
  const [hospitalCode, setHospitalCode] = useState("");
  const [loginName, setLoginName] = useState("");
  // PATIENT / MINISTRY shared username
  const [username, setUsername] = useState("");
  // shared
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  // Patient registration fields
  const [regNid, setRegNid] = useState("");
  const [regName, setRegName] = useState("");
  const [regDob, setRegDob] = useState("");
  const [regGender, setRegGender] = useState("MALE");
  const [regPhone, setRegPhone] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");

  // Load the active-hospital list for the doctor dropdown.
  useEffect(() => {
    api
      .getActiveOrganizations()
      .then((orgs) =>
        setHospitals(orgs.filter((o) => o.organization_type === "HOSPITAL")),
      )
      .catch(() => setHospitals([]));
  }, []);

  async function doLogin(e) {
    e?.preventDefault();
    setBusy(true);
    try {
      let credentials;
      if (tab === "DOCTOR") {
        credentials = {
          scope: "STAFF",
          org_code: hospitalCode.trim(),
          login_name: loginName.trim(),
          password,
        };
      } else if (tab === "PATIENT") {
        credentials = { scope: "PATIENT", username: username.trim(), password };
      } else {
        credentials = {
          scope: "MINISTRY",
          username: username.trim(),
          password,
        };
      }
      const signedIn = await login(credentials);
      show("Welcome back", "ok");
      // Return them to the protected page they originally asked for, otherwise
      // drop them on their role's dashboard. ProtectedRoute re-checks the role,
      // so a stale `from` for another portal is bounced to the right place.
      const from = location.state?.from?.pathname;
      navigate(from || dashboardPathFor(signedIn), { replace: true });
    } catch (err) {
      show(err.message, "err");
    } finally {
      setBusy(false);
    }
  }

  async function doRegister(e) {
    e?.preventDefault();
    setBusy(true);
    try {
      await api.registerPatient({
        nid: regNid.trim(),
        full_name: regName.trim(),
        date_of_birth: regDob,
        gender: regGender,
        phone: regPhone.trim(),
        email: regEmail.trim(),
        password: regPassword,
      });
      show("Registration successful — you can sign in now", "ok");
      // Prefill the sign-in form and switch to it.
      setUsername(regNid.trim());
      setPassword("");
      setPatientMode("SIGNIN");
    } catch (err) {
      show(err.message, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="landing-theme font-body-md text-on-surface bg-background">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-md shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
        <div className="h-20 max-w-container-max mx-auto px-margin-desktop flex items-center justify-between">
          <Brand size={36} />
          <nav className="hidden lg:flex items-center gap-stack-lg">
            <a
              className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors"
              href="#features"
            >
              About
            </a>
            <a
              className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors"
              href="#login-portal"
            >
              For Patients
            </a>
            <a
              className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors"
              href="#login-portal"
            >
              For Providers
            </a>
            <a
              className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors"
              href="#features"
            >
              Statistics
            </a>
          </nav>
          <a
            href="#login-portal"
            className="px-6 py-2 bg-primary text-on-primary rounded-lg font-label-md text-label-md hover:shadow-lg hover:shadow-primary/20 transition-all"
          >
            Sign In
          </a>
        </div>
      </header>

      <main className="w-full pt-20">
        {/* Hero + login */}
        <section className="relative overflow-hidden bg-surface py-24 md:py-28">
          <div className="absolute inset-0 z-0 opacity-10 pointer-events-none">
            <svg height="100%" width="100%" src="http://www.w3.org/2000/svg">
              <defs>
                <pattern
                  height="40"
                  id="grid"
                  patternUnits="userSpaceOnUse"
                  width="40"
                >
                  <path
                    className="text-primary"
                    d="M 40 0 L 0 0 0 40"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="0.5"
                  />
                </pattern>
              </defs>
              <rect fill="url(#grid)" height="100%" width="100%" />
            </svg>
          </div>
          <div className="max-w-container-max mx-auto px-margin-desktop relative z-10">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-stack-xl items-center">
              <div className="flex flex-col gap-stack-lg">
                <h1 className="font-display-lg text-display-lg text-on-surface max-w-xl">
                  All your health records in a single place.
                </h1>
                <p className="font-body-lg text-body-lg text-on-surface-variant max-w-lg">
                  Connecting citizens, hospitals, and the Ministry of Health
                  through a secure, federated national health data network
                  designed for clinical excellence.
                </p>
                <div className="flex flex-wrap gap-stack-md mt-stack-md">
                  <button
                    onClick={() => navigate("/activate")}
                    className="px-8 py-4 bg-primary text-on-primary rounded-xl font-title-lg shadow-xl hover:shadow-primary/20 transition-all flex items-center gap-stack-sm"
                  >
                    Activate Patient Account
                    <span className="material-symbols-outlined">
                      how_to_reg
                    </span>
                  </button>
                  <button
                    onClick={() => navigate("/register-org")}
                    className="px-8 py-4 bg-surface-container-lowest border-2 border-primary text-primary rounded-xl font-title-lg hover:bg-primary/5 transition-colors"
                  >
                    Register Organization
                  </button>
                </div>
              </div>

              {/* Login card */}
              <div
                id="login-portal"
                className="bg-surface-container-lowest p-stack-xl rounded-3xl border border-outline-variant shadow-2xl max-w-md w-full mx-auto lg:ml-auto"
              >
                <div className="text-center mb-6">
                  <h3 className="font-title-lg text-title-lg mb-2">
                    Portal Sign In
                  </h3>
                  <p className="text-body-md text-on-surface-variant">
                    Choose your role to continue
                  </p>
                </div>

                {/* Role tabs: Patient / Doctor / Ministry */}
                <div className="grid grid-cols-3 gap-1 p-1 bg-surface-container-low rounded-xl mb-6">
                  {[
                    { key: "PATIENT", label: "Patient" },
                    { key: "DOCTOR", label: "Doctor" },
                    { key: "MINISTRY", label: "Ministry" },
                  ].map((opt) => (
                    <button
                      key={opt.key}
                      type="button"
                      onClick={() => setTab(opt.key)}
                      className={`py-2 rounded-lg font-label-md text-label-md transition-colors ${
                        tab === opt.key
                          ? "bg-primary text-on-primary shadow"
                          : "text-on-surface-variant hover:bg-surface-container-high"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>

                {/* ---------------------------------------------------- PATIENT */}
                {tab === "PATIENT" && (
                  <>
                    {/* Sign In / Register sub-toggle */}
                    <div className="flex gap-1 p-1 bg-surface-container-low rounded-xl mb-6">
                      {[
                        { key: "SIGNIN", label: "Sign In" },
                        { key: "REGISTER", label: "Register" },
                      ].map((opt) => (
                        <button
                          key={opt.key}
                          type="button"
                          onClick={() => setPatientMode(opt.key)}
                          className={`flex-1 py-2 rounded-lg font-label-md text-label-md transition-colors ${
                            patientMode === opt.key
                              ? "bg-secondary text-on-secondary shadow"
                              : "text-on-surface-variant hover:bg-surface-container-high"
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>

                    {patientMode === "SIGNIN" && (
                      <form className="space-y-6" onSubmit={doLogin}>
                        <div>
                          <label className="label">National ID (NID)</label>
                          <div className="relative">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">
                              badge
                            </span>
                            <input
                              className="field pl-10"
                              placeholder="e.g. 12345678901"
                              value={username}
                              onChange={(e) => setUsername(e.target.value)}
                            />
                          </div>
                        </div>
                        <PasswordField
                          value={password}
                          onChange={setPassword}
                        />
                        <SubmitButton
                          busy={busy}
                          label="Sign In"
                          busyLabel="Signing in…"
                        />
                        <p className="text-center text-body-md text-on-surface-variant">
                          Have existing hospital records?{" "}
                          <button
                            type="button"
                            onClick={() => navigate("/activate")}
                            className="text-primary hover:underline"
                          >
                            Activate account
                          </button>
                        </p>
                      </form>
                    )}

                    {patientMode === "REGISTER" && (
                      <form className="space-y-4" onSubmit={doRegister}>
                        <div>
                          <label className="label">National ID (NID)</label>
                          <input
                            className="field"
                            placeholder="11-digit NID"
                            value={regNid}
                            onChange={(e) => setRegNid(e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="label">Full Name</label>
                          <input
                            className="field"
                            placeholder="Your full name"
                            value={regName}
                            onChange={(e) => setRegName(e.target.value)}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="label">Date of Birth</label>
                            <input
                              type="date"
                              className="field"
                              value={regDob}
                              onChange={(e) => setRegDob(e.target.value)}
                            />
                          </div>
                          <div>
                            <label className="label">Gender</label>
                            <select
                              className="field"
                              value={regGender}
                              onChange={(e) => setRegGender(e.target.value)}
                            >
                              <option value="MALE">Male</option>
                              <option value="FEMALE">Female</option>
                              <option value="OTHER">Other</option>
                            </select>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="label">Phone</label>
                            <input
                              className="field"
                              placeholder="Optional"
                              value={regPhone}
                              onChange={(e) => setRegPhone(e.target.value)}
                            />
                          </div>
                          <div>
                            <label className="label">Email</label>
                            <input
                              className="field"
                              placeholder="Optional"
                              value={regEmail}
                              onChange={(e) => setRegEmail(e.target.value)}
                            />
                          </div>
                        </div>
                        <div>
                          <label className="label">Password</label>
                          <input
                            type="password"
                            className="field"
                            placeholder="At least 6 characters"
                            value={regPassword}
                            onChange={(e) => setRegPassword(e.target.value)}
                          />
                        </div>
                        <SubmitButton
                          busy={busy}
                          label="Create Account"
                          busyLabel="Creating…"
                        />
                      </form>
                    )}
                  </>
                )}

                {/* ---------------------------------------------------- DOCTOR */}
                {tab === "DOCTOR" && (
                  <form className="space-y-6" onSubmit={doLogin}>
                    <div>
                      <label className="label">Hospital</label>
                      <div className="relative">
                        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline z-10">
                          apartment
                        </span>
                        <select
                          className="field pl-10"
                          value={hospitalCode}
                          onChange={(e) => setHospitalCode(e.target.value)}
                        >
                          <option value="">Select your hospital…</option>
                          {hospitals.map((h) => (
                            <option key={h.id} value={h.organization_code}>
                              {h.organization_name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="label">Username</label>
                      <div className="relative">
                        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">
                          person
                        </span>
                        <input
                          className="field pl-10"
                          placeholder="e.g. doctor"
                          value={loginName}
                          onChange={(e) => setLoginName(e.target.value)}
                        />
                      </div>
                    </div>
                    <PasswordField value={password} onChange={setPassword} />
                    <SubmitButton
                      busy={busy}
                      label="Sign In"
                      busyLabel="Signing in…"
                    />
                    <p className="text-center text-body-md text-on-surface-variant">
                      Your credentials are issued by your hospital
                      administrator.
                    </p>
                  </form>
                )}

                {/* --------------------------------------------------- MINISTRY */}
                {tab === "MINISTRY" && (
                  <form className="space-y-6" onSubmit={doLogin}>
                    <div>
                      <label className="label">Username</label>
                      <div className="relative">
                        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">
                          person
                        </span>
                        <input
                          className="field pl-10"
                          placeholder="e.g. superadmin"
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                        />
                      </div>
                    </div>
                    <PasswordField value={password} onChange={setPassword} />
                    <SubmitButton
                      busy={busy}
                      label="Sign In"
                      busyLabel="Signing in…"
                    />
                  </form>
                )}

                <div className="flex items-center gap-3 pt-6">
                  <div className="h-px flex-grow bg-outline-variant" />
                  <span className="text-label-sm uppercase tracking-widest text-on-surface-variant">
                    or
                  </span>
                  <div className="h-px flex-grow bg-outline-variant" />
                </div>
                <button
                  type="button"
                  onClick={() => navigate("/register-org")}
                  className="w-full mt-4 py-3 border-2 border-primary text-primary rounded-lg font-label-md hover:bg-primary/5 transition-colors"
                >
                  Register Organization
                </button>
              </div>
            </div>
          </div>
        </section>

        <ShowcaseBand navigate={navigate} />

        <StatsBand />

        {/* Features */}
        <section id="features" className="py-24 bg-surface">
          <div className="max-w-container-max mx-auto px-margin-desktop">
            <div className="flex flex-col gap-stack-sm mb-16 text-center max-w-2xl mx-auto">
              <span className="font-label-md text-label-md text-secondary uppercase tracking-[0.2em]">
                National Infrastructure
              </span>
              <h2 className="font-headline-lg text-headline-lg text-on-surface">
                Designed for Resilience and Reach
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-stack-xl">
              <Feature
                icon="fingerprint"
                title="Secure Identity"
                body="National ID (NID) integration ensures every health record is accurately linked to the right individual."
              />
              <Feature
                icon="travel_explore"
                title="Seamless Portability"
                body="Your records follow you across any province, so doctors can access your history instantly."
              />
              <Feature
                icon="clinical_notes"
                title="Empowered Doctors"
                body="Real-time access to longitudinal patient history reduces diagnostic errors and duplicate testing."
              />
            </div>
          </div>
        </section>

        {/* Security band */}
        <section className="py-24 bg-primary text-on-primary relative overflow-hidden">
          <div className="max-w-container-max mx-auto px-margin-desktop relative z-10">
            <div className="flex flex-col gap-stack-lg max-w-2xl">
              <h2 className="font-headline-lg text-headline-lg">
                Institutional Grade Security
              </h2>
              <p className="font-body-lg text-body-lg text-on-primary/80">
                NUHRS is governed by the Ministry of Health and Population,
                using end-to-end encryption and a federated data architecture so
                patient privacy is never compromised.
              </p>
              <div className="grid grid-cols-2 gap-stack-md">
                <Trust
                  icon="enhanced_encryption"
                  label="256-bit AES Encryption"
                />
                <Trust icon="policy" label="Privacy Compliant" />
                <Trust icon="account_balance" label="MoH Oversight" />
                <Trust icon="analytics" label="Audit Logging" />
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="w-full bg-surface-container-high border-t border-outline-variant py-stack-xl">
        <div className="max-w-container-max mx-auto px-margin-desktop flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">
              health_and_safety
            </span>
            <span className="font-headline-md text-[20px] text-primary">
              NUHRS
            </span>
          </div>
          <p className="text-body-md text-on-surface-variant">
            A government initiative for digital health sovereignty · Kathmandu,
            Nepal
          </p>
        </div>
      </footer>
    </div>
  );
}

function ShowcaseBand({ navigate }) {
  const [broken, setBroken] = useState(false);
  return (
    <section className="bg-surface-container-low py-24">
      <div className="max-w-container-max mx-auto px-margin-desktop">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-stack-xl items-center">
          {/* Copy on the left */}
          <div className="flex flex-col gap-stack-lg order-2 lg:order-1">
            <span className="font-label-md text-label-md text-secondary uppercase tracking-[0.2em]">
              One Network, Every Facility
            </span>
            <h2 className="font-headline-lg text-headline-lg text-on-surface max-w-lg">
              Hospitals, labs, and citizens — connected through a single secure
              exchange.
            </h2>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-lg">
              NUHRS federates data across providers so a patient's history
              travels with them. No silos, no duplicate tests, no lost records —
              just unified, secure access at the point of care.
            </p>
            <div className="flex flex-wrap gap-stack-md mt-stack-sm">
              <button
                onClick={() => navigate("/register-org")}
                className="px-8 py-4 bg-primary text-on-primary rounded-xl font-title-lg shadow-xl hover:shadow-primary/20 transition-all"
              >
                Join the Network
              </button>
            </div>
          </div>

          {/* Illustration on the right */}
          <div className="order-1 lg:order-2 flex justify-center lg:justify-end">
            {broken ? (
              <div className="w-full max-w-xl aspect-[16/10] rounded-3xl bg-primary/5 border border-outline-variant flex items-center justify-center">
                <span className="material-symbols-outlined text-primary text-[64px]">
                  hub
                </span>
              </div>
            ) : (
              <img
                src={background}
                alt="Unified health data network illustration"
                onError={() => setBroken(true)}
                className="w-full max-w-xl rounded-3xl shadow-2xl object-contain"
              />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function PasswordField({ value, onChange }) {
  return (
    <div>
      <label className="label">Password</label>
      <div className="relative">
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">
          lock
        </span>
        <input
          type="password"
          className="field pl-10"
          placeholder="••••••••"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    </div>
  );
}

function SubmitButton({ busy, label, busyLabel }) {
  return (
    <button
      type="submit"
      disabled={busy}
      className="w-full py-4 bg-primary text-on-primary rounded-xl font-title-lg shadow-lg shadow-primary/20 hover:opacity-90 transition-all disabled:opacity-50"
    >
      {busy ? busyLabel : label}
    </button>
  );
}

function Feature({ icon, title, body }) {
  return (
    <div className="group flex flex-col gap-stack-md p-stack-xl bg-surface-container-low rounded-2xl hover:bg-surface-container-high transition-all duration-300">
      <div className="w-16 h-16 bg-white rounded-xl shadow-md flex items-center justify-center group-hover:scale-110 transition-transform">
        <span className="material-symbols-outlined text-primary text-[32px]">
          {icon}
        </span>
      </div>
      <h3 className="font-title-lg text-title-lg text-on-surface">{title}</h3>
      <p className="font-body-md text-body-md text-on-surface-variant">
        {body}
      </p>
    </div>
  );
}

function Trust({ icon, label }) {
  return (
    <div className="flex items-center gap-stack-sm">
      <span className="material-symbols-outlined text-[20px]">{icon}</span>
      <span className="font-label-md">{label}</span>
    </div>
  );
}

function StatsBand() {
  const [patients, setPatients] = useState(0);
  const [facilities, setFacilities] = useState(0);

  useEffect(() => {
    let raf;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / 1600, 1);
      setPatients(p * 124);
      setFacilities(Math.floor(p * 840));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <section className="bg-surface py-stack-xl">
      <div className="max-w-container-max mx-auto px-margin-desktop">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter max-w-4xl mx-auto">
          <div className="flex items-center gap-stack-lg p-stack-lg bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant">
            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-[32px]">
                groups
              </span>
            </div>
            <div>
              <div className="font-display-lg text-[32px] text-on-surface tabular-nums">
                {(patients / 10).toFixed(1)}M
              </div>
              <div className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
                Verified Patients
              </div>
            </div>
          </div>
          <div className="flex items-center gap-stack-lg p-stack-lg bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant">
            <div className="w-14 h-14 rounded-full bg-secondary/10 flex items-center justify-center text-secondary">
              <span className="material-symbols-outlined text-[32px]">
                local_hospital
              </span>
            </div>
            <div>
              <div className="font-display-lg text-[32px] text-on-surface tabular-nums">
                {facilities}+
              </div>
              <div className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
                Active Facilities
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
