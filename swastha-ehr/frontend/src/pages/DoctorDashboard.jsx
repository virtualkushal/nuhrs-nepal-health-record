import { useEffect, useState } from "react";
import {
  Stethoscope,
  Loader2,
  AlertTriangle,
  FlaskConical,
  Pill,
  ClipboardList,
  ArrowLeft,
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import DashboardHeader from "../components/DashboardHeader";
import TrendChart from "../components/TrendChart";
import { ENCOUNTER_STATUS_LABELS } from "../constants";

// Doctor workspace: a queue of patients in the doctor's department who have had
// vitals taken, a clinical timeline per encounter, and panels to diagnose
// (ICD-10), order labs (from the catalog), and prescribe (allergy banner only).
export default function DoctorDashboard() {
  const { user, logout } = useAuth();
  const [queue, setQueue] = useState([]);
  const [active, setActive] = useState(null); // active encounter
  const [loading, setLoading] = useState(true);

  async function loadQueue() {
    setLoading(true);
    try {
      const res = await api.get("/v1/encounters/");
      setQueue(res.data.results || res.data);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { loadQueue(); }, []);

  if (active) {
    return (
      <div className="min-h-screen bg-surface-800">
        <DashboardHeader user={user} logout={logout} />
        <EncounterView
          encounter={active}
          onBack={() => { setActive(null); loadQueue(); }}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-800">
      <DashboardHeader user={user} logout={logout} />
      <main className="mx-auto max-w-6xl px-6 py-6">
        <h2 className="flex items-center gap-2 text-lg font-bold text-white">
          <Stethoscope className="h-5 w-5 text-blue-500" /> My patient queue
        </h2>
        {loading ? (
          <div className="mt-8 flex justify-center"><Loader2 className="h-6 w-6 animate-spin text-blue-500" /></div>
        ) : queue.length === 0 ? (
          <p className="mt-6 rounded-xl bg-surface-750 p-6 text-center text-sm text-gray-400 shadow-sm ring-1 ring-line">
            No patients waiting. Once a nurse records vitals, patients appear here.
          </p>
        ) : (
          <div className="mt-4 grid gap-3">
            {queue.map((e) => (
              <button key={e.id} onClick={() => setActive(e)}
                className="flex items-center justify-between rounded-xl bg-surface-750 p-4 text-left shadow-sm ring-1 ring-line hover:ring-blue-200">
                <div>
                  <p className="font-semibold text-white">{e.patient_name}</p>
                  <p className="text-xs text-gray-400">
                    {e.hospital_identifier} · {e.department_display} · {e.chief_complaint || "No complaint noted"}
                  </p>
                </div>
                <span className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-xs font-medium text-blue-300">
                  {ENCOUNTER_STATUS_LABELS[e.status]}
                </span>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function EncounterView({ encounter, onBack }) {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState("timeline");

  async function loadTimeline() {
    const res = await api.get(`/v1/patients/${encounter.patient}/timeline/`);
    setData(res.data);
  }
  useEffect(() => { loadTimeline(); }, [encounter.patient]);

  const patient = data?.patient;
  const allergies = patient?.allergies || [];

  return (
    <main className="mx-auto max-w-5xl px-6 py-6">
      <button onClick={onBack} className="mb-4 flex items-center gap-1 text-sm text-gray-400 hover:text-white">
        <ArrowLeft className="h-4 w-4" /> Back to queue
      </button>

      {patient && (
        <div className="rounded-2xl bg-surface-750 p-5 shadow-sm ring-1 ring-line">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">{patient.first_name} {patient.last_name}</h2>
              <p className="text-sm text-gray-400">
                {patient.hospital_identifier} · {patient.gender} · {patient.age} yrs · {patient.blood_group}
              </p>
            </div>
          </div>
          {allergies.length > 0 && (
            <div className="mt-4 flex items-start gap-2 rounded-lg bg-red-500/10 px-4 py-3 ring-1 ring-red-200">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-300" />
              <div>
                <p className="text-sm font-semibold text-red-300">Allergy alert</p>
                <p className="text-sm text-red-300">{allergies.join(", ")}</p>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        {[
          ["timeline", "Timeline", ClipboardList],
          ["diagnose", "Diagnose", Stethoscope],
          ["lab", "Order Lab", FlaskConical],
          ["prescribe", "Prescribe", Pill],
        ].map(([key, label, Icon]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium ${tab === key ? "bg-blue-600 text-white" : "bg-surface-750 text-gray-300 ring-1 ring-line"}`}>
            <Icon className="h-4 w-4" /> {label}
          </button>
        ))}
      </div>

      <div className="mt-4">
        {tab === "timeline" && <Timeline data={data} />}
        {tab === "diagnose" && <DiagnosePanel encounter={encounter} onDone={loadTimeline} />}
        {tab === "lab" && <OrderLabPanel encounter={encounter} onDone={loadTimeline} />}
        {tab === "prescribe" && <PrescribePanel encounter={encounter} onDone={loadTimeline} />}
      </div>
    </main>
  );
}

function Timeline({ data }) {
  if (!data) return <Loader2 className="mx-auto mt-6 h-6 w-6 animate-spin text-blue-500" />;
  return (
    <div className="space-y-4">
      {(data.trends || []).length > 0 && (
        <div className="rounded-2xl bg-surface-750 p-5 shadow-sm ring-1 ring-line">
          <h3 className="mb-3 font-semibold text-white">Lab trends</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {data.trends.map((t) => (
              <TrendChart key={t.test_code} points={t.points} unit={t.unit} label={t.test_name} />
            ))}

          </div>
        </div>
      )}
      <Panel title="Diagnoses" items={data.diagnoses} render={(d) => (
        <>{d.disease_name} <span className="text-xs text-gray-500">({d.icd10_code}) · {d.clinical_status}</span></>
      )} />
      <Panel title="Lab results" items={data.lab_results} render={(r) => (
        <>{r.test_name}: <b>{r.result_value ?? r.report_text}</b> {r.result_unit} {r.flag && r.flag !== "NORMAL" && <span className="text-red-300">({r.flag})</span>}</>
      )} />
      <Panel title="Prescriptions" items={data.prescriptions} render={(p) => (
        <>{p.medication_name} <span className="text-xs text-gray-500">· {p.status}</span></>
      )} />
    </div>
  );
}

function Panel({ title, items, render }) {
  return (
    <div className="rounded-2xl bg-surface-750 p-5 shadow-sm ring-1 ring-line">
      <h3 className="font-semibold text-white">{title}</h3>
      {!items || items.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">None on record.</p>
      ) : (
        <ul className="mt-2 space-y-1.5 text-sm text-gray-200">
          {items.map((it) => <li key={it.id} className="border-b border-line pb-1.5">{render(it)}</li>)}
        </ul>
      )}
    </div>
  );
}

function DiagnosePanel({ encounter, onDone }) {
  const [catalog, setCatalog] = useState([]);
  const [code, setCode] = useState("");
  const [notes, setNotes] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/v1/icd10/", { params: { department: encounter.department } })
      .then((r) => { const list = r.data.results; setCatalog(list); if (list[0]) setCode(list[0].code); });
  }, [encounter.department]);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setMsg("");
    try {
      await api.post("/v1/diagnoses/", { encounter: encounter.id, patient: encounter.patient, icd10_code: code, notes });
      setMsg("Diagnosis recorded."); setNotes(""); onDone();
    } catch { setMsg("Could not record diagnosis."); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-2xl bg-surface-750 p-5 shadow-sm ring-1 ring-line">
      <h3 className="font-semibold text-white">Record a diagnosis</h3>
      <select value={code} onChange={(e) => setCode(e.target.value)} className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm">
        {catalog.map((c) => <option key={c.code} value={c.code}>{c.code} — {c.name}</option>)}
      </select>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Clinical notes (optional)"
        className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm" rows={3} />
      {msg && <p className="text-sm text-gray-300">{msg}</p>}
      <button disabled={busy} className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60">
        {busy && <Loader2 className="h-4 w-4 animate-spin" />} Save diagnosis
      </button>
    </form>
  );
}

function OrderLabPanel({ encounter, onDone }) {
  const [catalog, setCatalog] = useState([]);
  const [code, setCode] = useState("");
  const [priority, setPriority] = useState("ROUTINE");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/v1/lab-catalog/").then((r) => { const list = r.data.results; setCatalog(list); if (list[0]) setCode(list[0].code); });
  }, []);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setMsg("");
    try {
      await api.post("/v1/lab-orders/", { encounter: encounter.id, patient: encounter.patient, test_code: code, priority });
      setMsg("Lab order sent to the queue."); onDone();
    } catch { setMsg("Could not create the order."); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-2xl bg-surface-750 p-5 shadow-sm ring-1 ring-line">
      <h3 className="font-semibold text-white">Order a lab test</h3>
      <select value={code} onChange={(e) => setCode(e.target.value)} className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm">
        {catalog.map((c) => <option key={c.code} value={c.code}>{c.name} ({c.category})</option>)}
      </select>
      <select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm">
        <option value="ROUTINE">Routine</option>
        <option value="URGENT">Urgent</option>
      </select>
      {msg && <p className="text-sm text-gray-300">{msg}</p>}
      <button disabled={busy} className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60">
        {busy && <Loader2 className="h-4 w-4 animate-spin" />} Send order
      </button>
    </form>
  );
}

function PrescribePanel({ encounter, onDone }) {
  const [medication, setMedication] = useState("");
  const [dosage, setDosage] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setMsg("");
    try {
      await api.post("/v1/prescriptions/", { encounter: encounter.id, patient: encounter.patient, medication_name: medication, dosage_instruction: dosage });
      setMsg("Prescription sent to the pharmacy queue."); setMedication(""); setDosage(""); onDone();
    } catch { setMsg("Could not create the prescription."); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-2xl bg-surface-750 p-5 shadow-sm ring-1 ring-line">
      <h3 className="font-semibold text-white">Write a prescription</h3>
      <p className="text-xs text-gray-500">Check the allergy banner above before prescribing.</p>
      <input value={medication} onChange={(e) => setMedication(e.target.value)} placeholder="Medication (e.g. Amlodipine 5mg)" required
        className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm" />
      <input value={dosage} onChange={(e) => setDosage(e.target.value)} placeholder="Dosage (e.g. 1 tablet once daily)" required
        className="w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm" />
      {msg && <p className="text-sm text-gray-300">{msg}</p>}
      <button disabled={busy} className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60">
        {busy && <Loader2 className="h-4 w-4 animate-spin" />} Send to pharmacy
      </button>
    </form>
  );
}
