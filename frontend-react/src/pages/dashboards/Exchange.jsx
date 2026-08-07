import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card } from "../../components/ui.jsx";
import PatientHeader from "../../components/PatientHeader.jsx";
import TabBar from "../../components/TabBar.jsx";
import SummaryTab from "../../components/SummaryTab.jsx";
import VitalsTrendsTab from "../../components/VitalsTrendsTab.jsx";
import LabReportsTab from "../../components/LabReportsTab.jsx";
import MedicationsTab from "../../components/MedicationsTab.jsx";
import ConditionsTab from "../../components/ConditionsTab.jsx";
import EncountersTab from "../../components/EncountersTab.jsx";
import ImmunizationsTab from "../../components/ImmunizationsTab.jsx";
import {
  extractPatient,
  extractBloodGroup,
  extractAllergies,
  extractDiagnosticReports,
} from "../../lib/fhirUtils.js";

// Doctor / lab-technician record exchange. Search by NID, then read a unified,
// cross-hospital clinical record as a tabbed dashboard: a triage-first Summary
// plus per-domain tabs. All data comes from the federated $everything bundle
// (each resource tagged with _source); no backend changes are needed.
export default function Exchange({ initialNid = "" }) {
  const { show } = useToast();
  const [nid, setNid] = useState(initialNid);
  const [patient, setPatient] = useState(null); // from lookupPatient (demographics)
  const [bundle, setBundle] = useState(null); // federated FHIR bundle
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("summary");

  // Search + fetch in one flow so the doctor lands straight on the Summary.
  async function runSearch(rawNid) {
    const clean = String(rawNid || "").trim();
    if (!clean) return;
    setNid(clean);
    setLoading(true);
    setError(null);
    setBundle(null);
    setActiveTab("summary");
    try {
      const p = await api.lookupPatient(clean);
      setPatient(p);
      const data = await api.fetchRecords(clean, "ALL");
      setBundle(data);
    } catch (e) {
      setError(e.message);
      show(e.message, "err");
    } finally {
      setLoading(false);
    }
  }

  // Derived clinical facts for the header + tab badge.
  const fhirPatient = useMemo(() => extractPatient(bundle), [bundle]);
  const bloodGroup = useMemo(() => extractBloodGroup(fhirPatient), [fhirPatient]);
  const allergyCount = useMemo(() => extractAllergies(bundle).length, [bundle]);
  const labReportCount = useMemo(() => extractDiagnosticReports(bundle).length, [bundle]);

  // Auto-run once when arriving with a pre-filled NID (from Doctor Home search).
  const autoRan = useRef(false);
  useEffect(() => {
    if (initialNid && !autoRan.current) {
      autoRan.current = true;
      runSearch(initialNid);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialNid]);

  // Initial state: no patient loaded yet — show the central search.
  if (!patient) {
    return (
      <div className="space-y-stack-lg">
        <Card
          title="Patient Record Exchange"
          subtitle="Search by National ID to retrieve a unified, longitudinal record from every participating facility."
        >
          <div className="flex items-center w-full bg-surface-container rounded-full px-4 py-1.5 border border-outline-variant">
            <span className="material-symbols-outlined text-on-surface-variant mr-2">
              fingerprint
            </span>
            <input
              className="bg-transparent border-none outline-none w-full text-on-surface font-body-md"
              placeholder="Search Patient by National ID (NID)…"
              value={nid}
              onChange={(e) => setNid(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch(nid)}
            />
            <button
              onClick={() => runSearch(nid)}
              disabled={loading}
              className="btn-primary ml-2 shrink-0"
            >
              {loading ? "Searching…" : "Search"}
            </button>
          </div>
        </Card>
        {error && (
          <Card>
            <p className="text-on-surface-variant">{error}</p>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PatientHeader
        patient={patient}
        bloodGroup={bloodGroup}
        allergyCount={allergyCount}
        onSearch={runSearch}
      />

      {loading && (
        <Card>
          <div className="flex items-center gap-3 text-on-surface-variant">
            <span className="material-symbols-outlined animate-spin">progress_activity</span>
            <span className="font-body-md">Contacting facilities across the network…</span>
          </div>
        </Card>
      )}

      {error && !loading && (
        <Card>
          <p className="text-on-surface-variant">{error}</p>
        </Card>
      )}

      {bundle && !loading && (
        <>
          <TabBar
            activeTab={activeTab}
            onTabChange={setActiveTab}
            labReportCount={labReportCount}
          />
          <div>
            {activeTab === "summary" && <SummaryTab bundle={bundle} onNavigate={setActiveTab} />}
            {activeTab === "vitals" && <VitalsTrendsTab bundle={bundle} />}
            {activeTab === "labs" && <LabReportsTab bundle={bundle} />}
            {activeTab === "medications" && <MedicationsTab bundle={bundle} />}
            {activeTab === "conditions" && <ConditionsTab bundle={bundle} />}
            {activeTab === "encounters" && <EncountersTab bundle={bundle} />}
            {activeTab === "immunizations" && <ImmunizationsTab bundle={bundle} />}
          </div>
        </>
      )}
    </div>
  );
}
