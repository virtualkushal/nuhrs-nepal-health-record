import { useState } from "react";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card, Table, Badge } from "../../components/ui.jsx";
import ResourceCard from "../../components/ResourceCard.jsx";

// Doctor / lab technician record exchange: search by NID, then fetch unified bundle.
export default function Exchange() {
  const { show } = useToast();
  const [nid, setNid] = useState("");
  const [result, setResult] = useState(null); // { patient, index }
  const [bundle, setBundle] = useState(null);
  const [searching, setSearching] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState(null);

  async function search() {
    if (!nid.trim()) return;
    setSearching(true);
    setResult(null);
    setBundle(null);
    setError(null);
    try {
      const patient = await api.lookupPatient(nid.trim());
      const index = await api.patientIndex(nid.trim());
      setResult({ patient, index });
    } catch (e) {
      setError(e.message);
    } finally {
      setSearching(false);
    }
  }

  async function fetchBundle() {
    setFetching(true);
    try {
      const data = await api.fetchRecords(nid.trim(), "ALL");
      setBundle(data);
    } catch (e) {
      show(e.message, "err");
    } finally {
      setFetching(false);
    }
  }

  return (
    <div className="space-y-stack-lg">
      <Card
        title="Patient Record Exchange"
        subtitle="Search by National ID to retrieve a unified record from every participating facility."
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            className="field md:col-span-3"
            placeholder="Enter patient NID e.g. NID-1001"
            value={nid}
            onChange={(e) => setNid(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
          />
          <button onClick={search} disabled={searching} className="btn-primary">
            {searching ? "Searching…" : "Search"}
          </button>
        </div>
      </Card>

      {error && (
        <Card><p className="text-on-surface-variant">{error}</p></Card>
      )}

      {result && (
        <Card>
          <h3 className="font-headline-lg text-[22px]">
            {result.patient.full_name}{" "}
            <span className="text-on-surface-variant text-body-md">{result.patient.nid}</span>
          </h3>
          <p className="text-on-surface-variant mb-4">
            DOB {result.patient.date_of_birth} · {result.patient.gender} · {result.patient.phone || ""}
          </p>
          <Table head={["Type", "Summary", "Source", "Date"]}>
            {result.index.length === 0 && (
              <tr><td colSpan={4} className="py-3 text-on-surface-variant">No records indexed</td></tr>
            )}
            {result.index.map((r, i) => (
              <tr key={i} className="border-b border-outline-variant/60">
                <td className="py-2 pr-4">{r.resource_type}</td>
                <td className="py-2 pr-4">{r.summary}</td>
                <td className="py-2 pr-4"><Badge>{r.organization_name}</Badge></td>
                <td className="py-2 pr-4">{r.service_date}</td>
              </tr>
            ))}
          </Table>
          <div className="mt-4">
            <button onClick={fetchBundle} disabled={fetching} className="btn-primary">
              {fetching ? "Contacting facilities…" : "Fetch full unified record"}
            </button>
          </div>
        </Card>
      )}

      {bundle && (
        <Card>
          <h3 className="font-headline-lg text-[22px] mb-4">
            Unified Clinical Record{" "}
            <span className="text-on-surface-variant text-body-md">{bundle.total} resource(s)</span>
          </h3>
          {(bundle.entry || []).length === 0 ? (
            <p className="text-on-surface-variant">No clinical data returned.</p>
          ) : (
            (bundle.entry || []).map((e, i) => <ResourceCard key={i} resource={e.resource} />)
          )}
        </Card>
      )}
    </div>
  );
}
