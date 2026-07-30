import { Link } from "react-router-dom";
import {
  HeartPulse,
  UserPlus,
  History,
  Share2,
  Stethoscope,
  ShieldCheck,
  Activity,
  ArrowRight,
  LogIn,
  Heart,
  Droplets,
  Utensils,
  Bug,
} from "lucide-react";
import { DEPARTMENTS } from "../constants";

// Icons for each hospital department (falls back to Activity).
const DEPT_ICONS = {
  ENDOCRINOLOGY: Activity,
  INTERNAL_MEDICINE: Stethoscope,
  NEPHROLOGY: Droplets,
  CARDIOLOGY: Heart,
  GASTROENTEROLOGY: Utensils,
  INFECTIOUS_DISEASES: Bug,
  HEMATOLOGY: Droplets,
};

// Inline illustration: the patient journey — Register → Diagnose → Track → Share.
function JourneyArt() {
  const steps = [
    { Icon: UserPlus, label: "Register" },
    { Icon: Stethoscope, label: "Diagnose" },
    { Icon: History, label: "Track" },
    { Icon: Share2, label: "Share" },
  ];
  return (
    <div className="flex flex-col gap-5">
      {steps.map(({ Icon, label }, i) => (
        <div key={label} className="relative flex items-center gap-4">
          {/* connector line to next node */}
          {i < steps.length - 1 && (
            <span className="absolute left-7 top-14 h-5 w-0.5 bg-gradient-to-b from-brand-500 to-brand-800" />
          )}
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-800 text-white shadow-lg shadow-brand-900/40">
            <Icon className="h-6 w-6" />
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest text-brand-400">
              Step {i + 1}
            </div>
            <div className="text-lg font-bold text-white">{label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}


export default function LandingPage() {
  const services = [
    {
      icon: UserPlus,
      title: "Register With Us",
      text: "Create your patient profile from home before you even reach the hospital — no queue, no paperwork.",
    },
    {
      icon: Stethoscope,
      title: "Get Diagnosed",
      text: "Doctors record ICD-10 diagnoses, order lab tests, and treat you across every department.",
    },
    {
      icon: History,
      title: "Track Your Records",
      text: "Every visit, diagnosis, lab result and medication is kept in one secure place you can revisit any time.",
    },
    {
      icon: Share2,
      title: "Share Across Hospitals",
      text: "Grant another hospital access to your records with your own approval — powered by the HL7 FHIR standard.",
    },
    {
      icon: ShieldCheck,
      title: "Safe & Private",
      text: "You stay in control. Records are only shared when you say yes, and allergies are flagged to every doctor.",
    },
    {
      icon: Activity,
      title: "Whole Hospital",
      text: "Reception, nursing, doctors, lab and pharmacy all work from one connected system.",
    },
  ];

  const stats = [
    { value: `${DEPARTMENTS.length}`, label: "Departments" },
    { value: "FHIR R4", label: "HL7 Standard" },
    { value: "ICD-10", label: "Diagnoses" },
    { value: "LOINC", label: "Lab Coding" },
  ];

  return (
    <div className="min-h-screen bg-surface-800 font-sans text-surface-50 antialiased">
      {/* ── Navigation ──────────────────────────────────────────────────── */}
      <nav className="fixed top-0 z-50 w-full border-b border-line bg-surface-800/80 backdrop-blur-md">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2">
            <HeartPulse className="h-7 w-7 text-brand-400" />
            <span className="font-display text-xl font-bold tracking-tight text-white">
              Swasthya<span className="text-brand-400">EHR</span>
            </span>
          </Link>

          <div className="hidden items-center gap-8 md:flex">
            <a href="#departments" className="text-sm font-medium text-gray-300 transition hover:text-white">Departments</a>
            <a href="#services" className="text-sm font-medium text-gray-300 transition hover:text-white">Services</a>
            <span className="flex items-center gap-2 rounded-full border border-line bg-surface-700 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-gray-300">
              <span className="h-2 w-2 animate-pulse rounded-full bg-brand-500"></span>
              FHIR-enabled
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/login" className="hidden rounded-full border border-line px-5 py-2.5 text-sm font-semibold text-white transition hover:border-brand-500/60 md:block">
              Login
            </Link>
            <Link
              to="/register"
              className="rounded-full bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand-900/40 transition hover:bg-brand-500"
            >
              Register
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="gradient-mesh relative flex min-h-screen items-center overflow-hidden pt-32 pb-20">
        <div className="relative z-10 mx-auto grid max-w-7xl items-center gap-12 px-6 lg:grid-cols-2">
          <div className="space-y-8">
            <h1 className="font-display text-4xl font-bold leading-tight text-white lg:text-6xl">
              Register, Get Diagnosed,{" "}
              <span className="text-brand-400">Track &amp; Share</span> Your Records
            </h1>
            <p className="max-w-lg text-xl leading-relaxed text-gray-300">
              Our system lets patients register once, get diagnosed with the
              doctor, track their health, and share their own data easily and
              in a standard way.
            </p>

            <div className="flex flex-wrap gap-4">
              <Link
                to="/register"
                className="flex items-center gap-2 rounded-full bg-brand-600 px-8 py-4 font-semibold text-white shadow-xl shadow-brand-900/40 transition hover:bg-brand-500"
              >
                <UserPlus className="h-4 w-4" />
                Register
              </Link>
              <Link
                to="/login"
                className="flex items-center gap-2 rounded-full border border-line bg-surface-800/60 px-8 py-4 font-semibold text-white backdrop-blur-sm transition hover:border-brand-500/60"
              >
                <LogIn className="h-4 w-4" />
                Login to system
              </Link>
            </div>
          </div>

          {/* patient journey illustration */}
          <div className="animate-float">
            <div className="glass-card rounded-3xl p-8">
              <JourneyArt />
              <p className="mt-6 border-t border-line pt-5 text-center text-sm text-gray-300">
                One simple journey — from sign-up to sharing your health data
                securely over the HL7 FHIR standard.
              </p>
            </div>
          </div>

        </div>
      </section>

      {/* ── Stats ───────────────────────────────────────────────────────── */}
      <section className="border-y border-line bg-surface-750 py-16">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 px-6 text-center md:grid-cols-4">
          {stats.map(({ value, label }) => (
            <div key={label} className="space-y-2">
              <div className="font-display text-4xl font-bold text-white md:text-5xl">{value}</div>
              <div className="text-xs font-semibold uppercase tracking-widest text-brand-400">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Departments (top priority) ──────────────────────────────────── */}
      <section id="departments" className="bg-surface-800 py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto mb-16 max-w-3xl text-center">
            <h2 className="font-display text-4xl font-bold text-white md:text-5xl">Our Departments</h2>
            <p className="mt-4 text-xl text-gray-400">
              Specialist care across every corner of the hospital.
            </p>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {DEPARTMENTS.map((d) => {
              const Icon = DEPT_ICONS[d.value] || Activity;
              return (
                <div
                  key={d.value}
                  className="flex items-center gap-4 rounded-2xl border border-line bg-surface-700 p-5 transition hover:border-brand-500/50 hover:bg-brand-900/30"
                >
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-800 to-brand-600 text-white">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-base font-semibold text-white">{d.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Services ────────────────────────────────────────────────────── */}
      <section id="services" className="bg-surface-750 py-28">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto mb-16 max-w-3xl text-center">
            <h2 className="font-display text-4xl font-bold text-white md:text-5xl">Services</h2>
            <p className="mt-4 text-xl text-gray-400">
              Everything a modern hospital needs, in one connected platform.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {services.map(({ icon: Icon, title, text }) => (
              <div
                key={title}
                className="rounded-3xl border border-line bg-surface-800 p-8 transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_40px_-15px_rgba(30,58,138,0.4)]"
              >
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-800 to-brand-600 text-white shadow-lg shadow-brand-900/40">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="mb-3 text-xl font-bold text-white">{title}</h3>
                <p className="leading-relaxed text-gray-400">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-900 via-brand-800 to-brand-600 py-28">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute left-0 top-0 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand-400 blur-3xl"></div>
          <div className="absolute bottom-0 right-0 h-96 w-96 translate-x-1/2 translate-y-1/2 rounded-full bg-brand-300 blur-3xl"></div>
        </div>
        <div className="relative z-10 mx-auto max-w-4xl px-6 text-center">
          <h2 className="mb-6 font-display text-4xl font-bold text-white md:text-5xl">
            Ready to join us and stay healthy?
          </h2>
          <p className="mb-10 text-xl text-brand-100">
            Register once and carry your medical history to any hospital.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/register"
              className="group inline-flex items-center gap-3 rounded-full bg-white px-10 py-5 text-lg font-bold text-brand-900 shadow-2xl transition hover:bg-brand-50"
            >
              Register now
              <ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" />
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center gap-3 rounded-full border border-white/40 px-10 py-5 text-lg font-bold text-white transition hover:bg-white/10"
            >
              Login to system
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-line bg-surface-900 pt-16 pb-10">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
            <div className="max-w-sm">
              <div className="mb-4 flex items-center gap-2">
                <HeartPulse className="h-6 w-6 text-brand-400" />
                <span className="font-display text-xl font-bold text-white">
                  Swasthya<span className="text-brand-400">EHR</span>
                </span>
              </div>
              <p className="text-sm leading-relaxed text-gray-400">
                One health record for every hospital — register, get diagnosed,
                track and share your records securely.
              </p>
            </div>
            <div className="flex flex-col gap-3 text-sm">
              <Link to="/login" className="text-gray-400 transition hover:text-brand-400">Login</Link>
              <Link to="/register" className="text-gray-400 transition hover:text-brand-400">Register as patient</Link>
              <Link to="/staff-register" className="text-gray-400 transition hover:text-brand-400">Staff account request</Link>
              <Link to="/hospital-b" className="text-gray-400 transition hover:text-brand-400">For other hospitals — access records</Link>
            </div>
          </div>
          <div className="border-t border-line pt-8 text-center text-sm text-gray-500">
            <p>© 2026 SwasthyaEHR. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
