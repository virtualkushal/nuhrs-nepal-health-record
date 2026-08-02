import { useState } from "react";
import { Building2, Loader2, Search, ShieldCheck } from "lucide-react";
import api from "../services/api";

// Standalone "Hospital B" interoperability demo. An external hospital requests a
// patient's record by National ID, the patient approves in their portal, and
// this page polls until it receives a human-readable FHIR Bundle. No login —
// this simulates a *different* hospital's system consuming our FHIR API.
export default function HospitalBViewer() {
  const [nid, setNid] = useState("");
  const [requestId, setRequestId] = useState(null);
  const [status, setStatus] = useState("");
  const [bundle, setBundle] = useState(null);
  const [error, setError] = useState("");
  const [polling, setPolling] = useState(false);

  function summarize(b) {
    const byType = {};
    for (const e of b.entry || []) {
      const t = e.resource?.resourceType;
      byType[t] = byType[t] || [];
      byType[t].push(e.resource);
    }
    return byType;
  }

  async function requestAccess(e) {
    e.preventDefault();
    setError("");
    setBundle(null);
    try {
      const res = await api.post("/v1/share/request/", {
        national_id: nid.trim(),
        requester_label: "Hospital B (Interoperability Demo)",
      });
      setRequestId(res.data.request_id);
      setStatus("PENDING");
    } catch {
      setError("Could not create the access request.");
    }
  }

  async function poll() {
    if (!requestId) return;
    setPolling(true);
    setError("");
    try {
      const res = await api.get(`/v1/share/request/${requestId}/`);
      if (res.data.resourceType === "Bundle") {
        setBundle(res.data);
        setStatus("APPROVED");
      } else {
        setStatus(res.data.status || "PENDING");
      }
    } catch (err) {
      const s = err?.response?.data?.status;
      setStatus(s || "DENIED");
      setError(s ? `Request ${s.toLowerCase()}.` : "Access not granted.");
    } finally {
      setPolling(false);
    }
  }

  const grouped = bundle ? summarize(bundle) : null;
  const patient = grouped?.Patient?.[0];

  return (
    <div className="min-h-screen bg-surface-700 px-4 py-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 p-2.5 shadow-sm">
            <Building2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Hospital B — Records Portal</h1>
            <p className="text-sm text-gray-400">Request a patient's records from SwasthyaEHR via FHIR</p>
          </div>
        </div>

        <form onSubmit={requestAccess} className="rounded-2xl bg-surface-750 p-6 shadow-sm ring-1 ring-line">
          <label className="mb-1 block text-sm font-medium text-gray-200">Patient National ID</label>
          <div className="flex gap-2">
            <input
              value={nid}
              onChange={(e) => setNid(e.target.value)}
              placeholder="e.g. 1234500001"
              required
              className="flex-1 rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button type="submit" className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
              <Search className="h-4 w-4" /> Request
            </button>
          </div>
          <p className="mt-2 flex items-center gap-1.5 text-xs text-gray-500">
            <ShieldCheck className="h-3.5 w-3.5" /> The patient must approve this request in their own portal.
          </p>
        </form>

        {requestId && !bundle && (
          <div className="mt-4 rounded-2xl bg-surface-750 p-6 text-center shadow-sm ring-1 ring-line">
            <p className="text-sm text-gray-300">
              Request status: <span className="font-semibold text-white">{status}</span>
            </p>
            <button onClick={poll} disabled={polling}
              className="mt-3 inline-flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-900 disabled:opacity-60">
              {polling && <Loader2 className="h-4 w-4 animate-spin" />}
              Check for approval
            </button>
            {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
          </div>
        )}

        {bundle && patient && (
          <div className="mt-4 space-y-4">
            <div className="rounded-2xl bg-surface-750 p-6 shadow-sm ring-1 ring-emerald-100">
              <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">Access granted</span>
              <h2 className="mt-3 text-lg font-bold text-white">
                {patient.name?.[0]?.text || `${patient.name?.[0]?.given?.[0]} ${patient.name?.[0]?.family}`}
              </h2>
              <p className="text-sm text-gray-400">
                {patient.gender} · DOB {patient.birthDate} · NID {patient.identifier?.[0]?.value}
              </p>
            </div>

            <Section title="Diagnoses (Conditions)" rows={(grouped.Condition || []).map((c) => ({
              main: c.code?.text || c.code?.coding?.[0]?.display,
              sub: c.code?.coding?.[0]?.code,
              meta: c.clinicalStatus?.coding?.[0]?.code,
            }))} />

            <Section title="Lab Results (Observations)" rows={(grouped.Observation || []).map((o) => ({
              main: o.code?.text,
              sub: o.valueQuantity ? `${o.valueQuantity.value} ${o.valueQuantity.unit}` : o.valueString,
              meta: o.interpretation?.[0]?.coding?.[0]?.display,
            }))} />

            <Section title="Medications (MedicationRequests)" rows={(grouped.MedicationRequest || []).map((m) => ({
              main: m.medicationCodeableConcept?.text,
              sub: m.dosageInstruction?.[0]?.text,
              meta: m.status,
            }))} />

            <Section title="Visits (Encounters)" rows={(grouped.Encounter || []).map((e) => ({
              main: e.serviceType?.text,
              sub: e.period?.start ? new Date(e.period.start).toLocaleDateString() : "",
              meta: e.status,
            }))} />
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ title, rows }) {
  return (
    <div className="rounded-2xl bg-surface-750 p-6 shadow-sm ring-1 ring-line">
      <h3 className="font-semibold text-white">{title}</h3>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">None on record.</p>
      ) : (
        <ul className="mt-3 divide-y divide-line">
          {rows.map((r, i) => (
            <li key={i} className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium text-white">{r.main}</p>
                {r.sub && <p className="text-xs text-gray-400">{r.sub}</p>}
              </div>
              {r.meta && <span className="rounded-full bg-surface-700 px-2.5 py-0.5 text-xs font-medium text-gray-300">{r.meta}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
