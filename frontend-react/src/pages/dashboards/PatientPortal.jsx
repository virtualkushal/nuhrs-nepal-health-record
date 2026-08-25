import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card } from "../../components/ui.jsx";
import UserChangePassword from "../../components/UserChangePassword.jsx";
import TabBar from "../../components/TabBar.jsx";
import VitalsTrendsTab from "../../components/VitalsTrendsTab.jsx";
import { extractPatient, extractBloodGroup } from "../../lib/fhirUtils.js";
import HealthCardHeader from "../../components/patient/HealthCardHeader.jsx";
import VitalsCards from "../../components/patient/VitalsCards.jsx";
import CareSummary from "../../components/patient/CareSummary.jsx";
import AllergiesConditions from "../../components/patient/AllergiesConditions.jsx";
import RecentVisits from "../../components/patient/RecentVisits.jsx";
import HealthJourney from "../../components/patient/HealthJourney.jsx";
import LabResultsFriendly from "../../components/patient/LabResultsFriendly.jsx";
import MyMedications from "../../components/patient/MyMedications.jsx";
import ImmunizationsFriendly from "../../components/patient/ImmunizationsFriendly.jsx";
import AnnouncementsFeed from "../../components/patient/AnnouncementsFeed.jsx";
import PrintableRecord from "../../components/patient/PrintableRecord.jsx";

// The patient's own health record — a warm, lay-person view of the same FHIR
// bundle the doctor sees, fetched from the self-scoped /patient/bundle/ endpoint
// (NID derived from the session server-side). Reuses the fhirUtils parsers but
// presents them simpler than the clinician tabs, in the mock's blue/gold theme
// (scoped to the `.patient-theme` wrapper only).

const PATIENT_TABS = [
  { key: "overview", label: "Overview", icon: "dashboard" },
  { key: "vitals", label: "Vitals", icon: "monitoring" },
  { key: "labs", label: "Lab Results", icon: "science" },
  { key: "medications", label: "Medications", icon: "medication" },
  { key: "visits", label: "Visits", icon: "local_hospital" },
  { key: "immunizations", label: "Immunizations", icon: "vaccines" },
  { key: "settings", label: "Settings", icon: "settings" },
];

// A soft, friendly panel wrapper for the Overview bento cells.
function Panel({ icon, title, action, className = "", children }) {
  return (
    <div
      className={`bg-surface-container-lowest rounded-2xl shadow-sm border border-outline-variant/30 p-6 ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            {icon && <span className="material-symbols-outlined text-primary text-[20px]">{icon}</span>}
            <h2 className="font-headline-md text-[18px] text-on-surface">{title}</h2>
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

// Lazily create (once) the `#print-root` container as a DIRECT child of <body>.
// Mounting the printable record here — rather than deep inside #root — is what
// lets the print stylesheet collapse the whole app shell with
// `body > *:not(#print-root) { display: none }`. Collapsing instead of hiding
// removes the empty leading pages that `visibility: hidden` used to leave behind
// (hidden elements keep their layout box and still paginate).
function usePrintRoot() {
  const [node, setNode] = useState(null);

  useEffect(() => {
    let el = document.getElementById("print-root");
    if (!el) {
      el = document.createElement("div");
      el.id = "print-root";
      document.body.appendChild(el);
    }
    setNode(el);
    // Intentionally left in the DOM on unmount: it is a shared, empty, inert
    // container (styles keep it off-canvas), so repeated mounts stay cheap and
    // we never race a pending print dialog.
  }, []);

  return node;
}

export default function PatientPortal() {
  const { show } = useToast();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("overview");
  const printRoot = usePrintRoot();

  useEffect(() => {
    api
      .myBundle()
      .then(setData)
      .catch((e) => {
        setError(e.message);
        show(e.message, "err");
      });
  }, []);

  const bundle = data?.bundle;
  const patient = data?.patient;
  const bloodGroup = useMemo(
    () => (bundle ? extractBloodGroup(extractPatient(bundle)) : null),
    [bundle]
  );

  // Print-to-PDF: the browser's own "Save as PDF" acting on the PrintableRecord
  // document portalled into #print-root (no extra dependency).
  function savePdf() {
    if (bundle) window.print();
  }

  // Secondary raw-data export for portability.
  function downloadJson() {
    if (!bundle) return;
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `health-records-${patient?.nid || "me"}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  if (error && !data) {
    return (
      <div className="patient-theme">
        <Card title="My Health Record">
          <p className="text-error">{error}</p>
        </Card>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="patient-theme">
        <Card title="My Health Record">
          <p className="text-on-surface-variant">Loading your health record…</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="patient-theme space-y-stack-lg">
      <HealthCardHeader
        patient={patient}
        bloodGroup={bloodGroup}
        onDownloadPdf={savePdf}
        onDownloadJson={downloadJson}
      />
      <TabBar activeTab={tab} onTabChange={setTab} tabs={PATIENT_TABS} />

      {tab === "overview" && (
        <div className="space-y-stack-lg">
          <CareSummary bundle={bundle} />
          <Panel icon="health_and_safety" title="Allergies & Conditions">
            <AllergiesConditions bundle={bundle} />
          </Panel>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-gutter">
            <Panel icon="local_hospital" title="Recent Visits" className="lg:col-span-3">
              <RecentVisits bundle={bundle} limit={5} />
            </Panel>
            <Panel icon="timeline" title="Health Journey" className="lg:col-span-2">
              <HealthJourney bundle={bundle} limit={6} />
            </Panel>
          </div>
          <Panel icon="campaign" title="National Health Updates">
            <p className="text-body-md text-on-surface-variant -mt-2 mb-4">
              News and announcements from the Ministry of Health.
            </p>
            <AnnouncementsFeed />
          </Panel>
        </div>
      )}

      {tab === "vitals" && (
        <div className="space-y-stack-lg">
          <VitalsCards bundle={bundle} />
          <VitalsTrendsTab bundle={bundle} />
        </div>
      )}

      {tab === "labs" && <LabResultsFriendly bundle={bundle} />}

      {tab === "medications" && <MyMedications bundle={bundle} />}

      {tab === "visits" && (
        <Panel icon="local_hospital" title="Your Visits">
          <RecentVisits bundle={bundle} />
        </Panel>
      )}

      {tab === "immunizations" && <ImmunizationsFriendly bundle={bundle} />}

      {tab === "settings" && (
        <Panel icon="settings" title="Account Settings">
          <UserChangePassword />
        </Panel>
      )}

      {/* Printable document powering "Save as PDF". Portalled into #print-root
          (a direct child of <body>) so the print stylesheet can collapse the
          rest of the app instead of merely hiding it. */}
      {printRoot &&
        createPortal(
          <PrintableRecord patient={patient} bloodGroup={bloodGroup} bundle={bundle} />,
          printRoot
        )}
    </div>
  );
}
