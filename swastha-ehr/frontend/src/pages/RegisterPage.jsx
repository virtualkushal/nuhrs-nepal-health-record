import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import api from "../services/api";
import PatientForm from "../components/PatientForm";
import BrandMark from "../components/BrandMark";
import AuthArtwork from "../components/AuthArtwork";

// Public self-registration (REQ-001). No login required — a patient fills this
// from home before their appointment and receives a hospital identifier.
export default function RegisterPage() {
  const [done, setDone] = useState(null); // holds the created patient on success

  async function handleSubmit(payload) {
    const res = await api.post("/v1/patients/register/", payload);
    setDone(res.data);
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* left: form */}
      <div className="flex items-center justify-center bg-surface-700 p-6 sm:p-10">
        <div className="w-full max-w-lg">
          <div className="mb-8">
            <BrandMark subtitle="Patient self-registration" />
          </div>

          {done ? (
            <div className="rounded-2xl border border-line bg-surface-750 p-8 text-center shadow-sm">
              <CheckCircle2 className="mx-auto mb-3 h-12 w-12 text-brand-400" />
              <h2 className="text-lg font-semibold text-white">
                Registration complete
              </h2>
              <p className="mt-1 text-gray-300">
                Please show this ID at the front desk:
              </p>
              <p className="mt-3 font-mono text-2xl font-semibold text-brand-300">
                {done.hospital_identifier}
              </p>
              {done.has_login ? (
                <p className="mt-4 text-sm text-gray-300">
                  Your portal login is ready.{" "}
                  <Link to="/login" className="text-brand-300 hover:underline">
                    Sign in
                  </Link>{" "}
                  to view your lab results and medications.
                </p>
              ) : (
                <p className="mt-4 text-xs text-gray-500">
                  Tip: register with a username &amp; password next time to
                  access your online patient portal.
                </p>
              )}
              <button
                onClick={() => setDone(null)}
                className="mt-6 text-sm text-brand-300 hover:underline"
              >
                Register another patient
              </button>
            </div>
          ) : (
            <>
              <h2 className="text-2xl font-bold text-white">
                Create your patient profile
              </h2>
              <p className="mb-6 mt-1 text-sm text-gray-400">
                You'll get a hospital ID to present at reception, and can
                optionally create a login to view your records online.
              </p>
              <div className="rounded-2xl border border-line bg-surface-750 p-6 shadow-sm">
                <PatientForm
                  onSubmit={handleSubmit}
                  submitLabel="Register"
                  withCredentials
                />
              </div>
              <p className="mt-6 text-center text-sm text-gray-400">
                Already registered or hospital staff?{" "}
                <Link to="/login" className="font-medium text-brand-300 hover:underline">
                  Sign in
                </Link>
              </p>
            </>
          )}
        </div>
      </div>

      {/* right: artwork */}
      <AuthArtwork />
    </div>
  );
}
