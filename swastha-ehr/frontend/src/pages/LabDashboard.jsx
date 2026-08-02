import { useEffect, useState } from "react";
import { FlaskConical, CheckCircle2, Loader2, ClipboardList } from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import DashboardHeader from "../components/DashboardHeader";
import { ROLE_THEME } from "../constants";

// Lab Technician station: work the pending order queue and submit a result for
// each. The catalog tells us whether the test is QUANTITATIVE (numeric value)
// or QUALITATIVE (a text report). The backend flags high/low automatically.
export default function LabDashboard() {
  const { user, logout } = useAuth();
  const [orders, setOrders] = useState([]);
  const [catalog, setCatalog] = useState({});
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadQueue() {
    setLoading(true);
    try {
      const [ordersRes, catRes] = await Promise.all([
        api.get("/v1/lab-orders/"),
        api.get("/v1/lab-catalog/"),
      ]);
      setOrders(ordersRes.data.results || ordersRes.data);
      const map = {};
      (catRes.data.results || []).forEach((c) => { map[c.code] = c; });
      setCatalog(map);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { loadQueue(); }, []);

  return (
    <div className={`min-h-screen bg-gradient-to-b ${ROLE_THEME.LAB_TECH.tint}`}>
      <DashboardHeader user={user} logout={logout} subtitle="Diagnostic lab station" />
      <main className="mx-auto grid max-w-4xl gap-6 p-6 md:grid-cols-2">
        <section className="rounded-2xl border border-line bg-surface-750 p-5 shadow-sm">
          <h2 className="mb-3 flex items-center gap-2 font-semibold text-white">
            <ClipboardList className="h-5 w-5 text-violet-300" /> Pending orders
          </h2>
          {loading ? (
            <div className="flex justify-center py-10 text-gray-500"><Loader2 className="h-6 w-6 animate-spin" /></div>
          ) : (
            <ul className="max-h-96 divide-y divide-line overflow-y-auto">
              {orders.map((o) => (
                <li key={o.id}>
                  <button onClick={() => setSelected(o)}
                    className={`w-full rounded-lg px-3 py-3 text-left transition-colors ${selected?.id === o.id ? "bg-violet-500/20" : "hover:bg-surface-700"}`}>
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-white">{o.test_name}</p>
                      {o.priority === "URGENT" && (
                        <span className="rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-semibold text-red-300">URGENT</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-400">{o.patient_name}</p>
                    <p className="font-mono text-xs text-gray-500">{o.category} · LOINC {o.loinc_code || "—"}</p>
                  </button>
                </li>
              ))}
              {orders.length === 0 && (
                <li className="px-3 py-8 text-center text-sm text-gray-500">No pending orders. All caught up!</li>
              )}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-line bg-surface-750 p-5 shadow-sm">
          {selected ? (
            <ResultEntryPanel order={selected} meta={catalog[selected.test_code]} onSaved={() => { setSelected(null); loadQueue(); }} />
          ) : (
            <div className="flex h-full flex-col items-center justify-center py-12 text-center text-gray-500">
              <FlaskConical className="mb-2 h-8 w-8" />
              <p>Select an order to enter its result.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function ResultEntryPanel({ order, meta, onSaved }) {
  const [value, setValue] = useState("");
  const [reportText, setReportText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const isQuantitative = meta?.type === "QUANTITATIVE";

  useEffect(() => { setValue(""); setReportText(""); setError(""); setSuccess(""); }, [order.id]);

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true); setError(""); setSuccess("");
    try {
      const result = { test_code: order.test_code };
      if (isQuantitative) result.result_value = value;
      else result.report_text = reportText;
      await api.post("/v1/lab-reports/", { lab_order: order.id, results: [result] });
      setSuccess("Result recorded and order closed.");
      setTimeout(onSaved, 700);
    } catch (err) {
      const data = err?.response?.data;
      const first = data && typeof data === "object" ? Object.values(data)[0] : null;
      setError(Array.isArray(first) ? first[0] : first || "Could not save the result.");
    } finally {
      setBusy(false);
    }
  }

  const field = "w-full rounded-lg border border-line bg-surface-800 text-white placeholder-gray-500 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-500";

  return (
    <div>
      <h2 className="font-semibold text-white">{order.test_name}</h2>
      <p className="mb-1 text-sm text-gray-400">{order.patient_name}</p>
      <p className="mb-4 font-mono text-xs text-gray-500">{order.category} · LOINC {order.loinc_code || "—"}</p>

      {isQuantitative && meta && (meta.reference_low != null || meta.reference_high != null) && (
        <div className="mb-4 rounded-lg border border-line bg-surface-700 px-3 py-2 text-sm text-gray-300">
          Reference range: <span className="font-medium text-white">{meta.reference_low}–{meta.reference_high} {meta.unit}</span>
        </div>
      )}
      {error && <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</div>}
      {success && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-brand-500/30 bg-brand-500/10 px-3 py-2 text-sm text-teal-800">
          <CheckCircle2 className="h-5 w-5" /> {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        {isQuantitative ? (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-200">Result value {meta?.unit ? `(${meta.unit})` : ""}</label>
            <input type="number" step="0.01" className={field} value={value} onChange={(e) => setValue(e.target.value)} placeholder="e.g. 14.20" required />
          </div>
        ) : (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-200">Report / conclusion</label>
            <textarea className={field} rows={4} value={reportText} onChange={(e) => setReportText(e.target.value)} placeholder="e.g. No abnormality detected." required />
          </div>
        )}
        <button type="submit" disabled={busy}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2.5 font-medium text-white hover:bg-violet-700 disabled:opacity-60">
          {busy && <Loader2 className="h-5 w-5 animate-spin" />}
          {busy ? "Saving…" : "Submit result"}
        </button>
      </form>
    </div>
  );
}
