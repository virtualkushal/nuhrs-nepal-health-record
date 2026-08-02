import { useEffect, useState } from "react";
import { Search, UserPlus, CheckCircle2, LogIn } from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import PatientForm from "../components/PatientForm";
import DashboardHeader from "../components/DashboardHeader";
import { DEPARTMENTS } from "../constants";

// Receptionist front desk: search/register patients and check them in for a
// visit (create an encounter) which routes them to the nurse then the doctor.
export default function ReceptionDashboard() {
  const { user, logout } = useAuth();
  const [search, setSearch] = useState("");
  const [patients, setPatients] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [checkIn, setCheckIn] = useState(null); // patient being checked in
  const [flash, setFlash] = useState("");

  async function load(query = "") {
    const res = await api.get("/v1/patients/", { params: query ? { search: query } : {} });
    setPatients(res.data.results || res.data);
  }
  useEffect(() => { load(); }, []);

  async function handleCreate(payload) {
    const res = await api.post("/v1/patients/", payload);
    setFlash(`Registered ${res.data.first_name} — ${res.data.hospital_identifier}`);
    setShowForm(false);
    load(search);
  }

  return (
    <div className="min-h-screen bg-surface-800">
      <DashboardHeader user={user} logout={logout} subtitle="Front desk" />
      <main className="mx-auto max-w-4xl p-6">
        {flash && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-brand-500/30 bg-brand-500/10 px-4 py-3 text-teal-800">
            <CheckCircle2 className="h-5 w-5" /> {flash}
          </div>
        )}

        <div className="mb-4 flex items-center justify-between">
          <form onSubmit={(e) => { e.preventDefault(); load(search); }} className="flex max-w-md flex-1 items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <input value={search} onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, NID, phone or hospital ID"
                className="w-full rounded-lg border border-line py-2 pl-9 pr-3 focus:outline-none focus:ring-2 focus:ring-brand-500" />
            </div>
          </form>
          <button onClick={() => setShowForm((s) => !s)}
            className="ml-3 flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-500">
            <UserPlus className="h-4 w-4" /> {showForm ? "Close" : "New patient"}
          </button>
        </div>

        {showForm && (
          <div className="mb-6 rounded-2xl border border-line bg-surface-750 p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-white">Register patient</h2>
            <PatientForm onSubmit={handleCreate} submitLabel="Register patient" withCredentials />
          </div>
        )}

        <div className="overflow-hidden rounded-2xl border border-line bg-surface-750 shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-surface-700 text-left text-gray-400">
              <tr>
                <th className="px-4 py-3 font-medium">Hospital ID</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Phone</th>
                <th className="px-4 py-3 font-medium">Allergies</th>
                <th className="px-4 py-3 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <tr key={p.id} className="border-t border-line">
                  <td className="px-4 py-3 font-mono text-gray-200">{p.hospital_identifier}</td>
                  <td className="px-4 py-3 text-white">{p.first_name} {p.last_name}</td>
                  <td className="px-4 py-3 text-gray-300">{p.phone_number}</td>
                  <td className="px-4 py-3 text-gray-300">{p.allergies?.length ? p.allergies.join(", ") : "None"}</td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => setCheckIn(p)}
                      className="inline-flex items-center gap-1 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-500">
                      <LogIn className="h-3.5 w-3.5" /> Check in
                    </button>
                  </td>
                </tr>
              ))}
              {patients.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No patients found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </main>

      {checkIn && (
        <CheckInModal patient={checkIn} onClose={() => setCheckIn(null)}
          onDone={(name) => { setCheckIn(null); setFlash(`${name} checked in — sent to the nurse for vitals.`); }} />
      )}
    </div>
  );
}

function CheckInModal({ patient, onClose, onDone }) {
  const [department, setDepartment] = useState(DEPARTMENTS[0].value);
  const [doctors, setDoctors] = useState([]);
  const [doctorId, setDoctorId] = useState("");
  const [complaint, setComplaint] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/v1/auth/staff/", { params: { role: "DOCTOR" } })
      .then((r) => setDoctors((r.data.results || r.data).filter((d) => d.department === department)))
      .catch(() => setDoctors([]));
    setDoctorId("");
  }, [department]);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const payload = { patient: patient.id, department, chief_complaint: complaint };
      if (doctorId) payload.attending_doctor = doctorId;
      await api.post("/v1/encounters/", payload);
      onDone(patient.first_name);
    } catch (err) {
      const d = err?.response?.data;
      const first = d && typeof d === "object" ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? first[0] : first || "Could not check in the patient.");
    } finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/40 px-4">
      <form onSubmit={submit} className="w-full max-w-md space-y-3 rounded-2xl bg-surface-750 p-6 shadow-xl">
        <h3 className="text-lg font-bold text-white">Check in — {patient.first_name} {patient.last_name}</h3>
        {error && <div className="rounded-lg bg-red-500/10 px-4 py-2 text-sm text-red-300">{error}</div>}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-200">Department</label>
          <select value={department} onChange={(e) => setDepartment(e.target.value)}
            className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm">
            {DEPARTMENTS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-200">Attending doctor (optional)</label>
          <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)}
            className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm">
            <option value="">Any available</option>
            {doctors.map((d) => <option key={d.id} value={d.id}>{d.full_name}</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-200">Chief complaint</label>
          <textarea value={complaint} onChange={(e) => setComplaint(e.target.value)} rows={2}
            className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm" placeholder="e.g. Fever and cough for 3 days" />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="rounded-lg px-4 py-2 text-sm text-gray-300 hover:bg-surface-700">Cancel</button>
          <button type="submit" disabled={busy} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-500 disabled:opacity-60">
            {busy ? "Checking in…" : "Confirm check-in"}
          </button>
        </div>
      </form>
    </div>
  );
}
