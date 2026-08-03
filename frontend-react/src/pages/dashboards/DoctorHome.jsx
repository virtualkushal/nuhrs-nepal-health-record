import { useEffect, useState } from "react";
import { api } from "../../lib/api.js";
import { useAuth } from "../../context/AuthContext.jsx";

// Doctor Dashboard — Home (Stitch "Doctor Dashboard - Home (Desktop)").
// A landing view the doctor sees before drilling into a patient's unified
// record. The central NID search hands off to the grouped-records Exchange
// view via the `onSearch` callback.
export default function DoctorHome({ onSearch }) {
  const { user } = useAuth();
  const [nid, setNid] = useState("");
  const [invalid, setInvalid] = useState(false);
  const [facilities, setFacilities] = useState([]);
  const [recents, setRecents] = useState([]);

  const doctorName = user?.full_name || user?.username || "Doctor";
  const orgName = user?.organization_name || "Your Facility";

  // Pull live network facilities + recent audit activity where available.
  useEffect(() => {
    (async () => {
      try {
        const orgs = await api.listOrgs("APPROVED");
        setFacilities(Array.isArray(orgs) ? orgs.slice(0, 5) : []);
      } catch {
        setFacilities([]);
      }
      try {
        const events = await api.audit();
        // De-dupe recently accessed patients by NID from the audit trail.
        const seen = new Map();
        for (const e of Array.isArray(events) ? events : []) {
          const key = e.patient_nid || e.nid;
          if (key && !seen.has(key)) {
            seen.set(key, {
              nid: key,
              name: e.patient_name || e.patient || key,
              when: e.created_at || e.timestamp || "",
              action: e.action || "Accessed",
            });
          }
        }
        setRecents([...seen.values()].slice(0, 5));
      } catch {
        setRecents([]);
      }
    })();
  }, []);

  function submit() {
    const clean = nid.replace(/\D/g, "");
    if (!clean) {
      setInvalid(true);
      setTimeout(() => setInvalid(false), 1500);
      return;
    }
    onSearch?.(clean);
  }

  const initials = (name) =>
    name
      .split(/\s+/)
      .slice(0, 2)
      .map((w) => w[0]?.toUpperCase())
      .join("");

  return (
    <div className="flex flex-col w-full gap-gutter">
      {/* Hero: doctor profile */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-stretch">
        <div className="lg:col-span-8 relative overflow-hidden rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/30 flex flex-col md:flex-row items-center p-8 gap-8">
          <div className="relative z-10 flex-shrink-0">
            <div className="w-32 h-32 md:w-36 md:h-36 rounded-full border-4 border-primary/10 bg-primary/5 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-[72px]">
                stethoscope
              </span>
            </div>
            <div className="absolute -bottom-2 -right-2 bg-secondary/10 text-secondary px-3 py-1 rounded-full font-label-sm text-label-sm shadow-sm flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">verified</span>
              Verified
            </div>
          </div>
          <div className="relative z-10 text-center md:text-left flex-1">
            <span className="font-label-md text-label-md text-primary uppercase tracking-widest">
              {user?.role === "LAB_TECHNICIAN" ? "Lab Technician" : "Consultant Physician"}
            </span>
            <h1 className="font-headline-lg text-[32px] text-on-surface mt-1">
              {doctorName}
            </h1>
            <div className="flex items-center justify-center md:justify-start gap-4 mt-3 flex-wrap">
              <div className="flex items-center gap-2 text-on-surface-variant">
                <span className="material-symbols-outlined text-primary text-[18px]">
                  account_balance
                </span>
                <span className="font-label-md text-label-md">{orgName}</span>
              </div>
              {user?.username && (
                <>
                  <div className="w-1 h-1 rounded-full bg-outline-variant" />
                  <div className="flex items-center gap-2 text-on-surface-variant">
                    <span className="material-symbols-outlined text-primary text-[18px]">
                      badge
                    </span>
                    <span className="font-label-md text-label-md">
                      ID: {user.username}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-primary/5 to-transparent rounded-bl-full -mr-24 -mt-24 pointer-events-none" />
        </div>

        {/* Quick stats */}
        <div className="lg:col-span-4 grid grid-cols-2 gap-4">
          <StatTile
            icon="groups"
            value={recents.length}
            label="Recent Patients"
          />
          <StatTile
            icon="lan"
            value={facilities.length}
            label="Connected Facilities"
            tone="secondary"
          />
          <StatTile icon="clinical_notes" value="—" label="Open Reviews" />
          <StatTile
            icon="verified_user"
            value="Secure"
            label="Session"
            tone="secondary"
          />
        </div>
      </section>

      {/* Central patient search */}
      <section className="bg-primary rounded-2xl p-8 shadow-xl relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          <svg fill="none" height="100%" width="100%" xmlns="http://www.w3.org/2000/svg">
            <pattern height="40" id="dh-grid" patternUnits="userSpaceOnUse" width="40">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1" />
            </pattern>
            <rect fill="url(#dh-grid)" height="100%" width="100%" />
          </svg>
        </div>
        <div className="relative z-10 max-w-3xl mx-auto text-center flex flex-col items-center gap-6">
          <div className="flex flex-col gap-2">
            <h2 className="font-headline-lg text-[32px] text-on-primary">
              Patient Central Registry Access
            </h2>
            <p className="font-body-md text-body-md text-on-primary/80">
              Enter a National Health ID (NID) to fetch the unified medical
              history across all interconnected facilities.
            </p>
          </div>
          <div
            className={`w-full bg-white/10 backdrop-blur-md p-2 rounded-2xl flex items-center gap-2 transition-all ${
              invalid ? "ring-2 ring-error" : "focus-within:bg-white/20"
            }`}
          >
            <div className="flex-1 flex items-center px-4 gap-4">
              <span className="material-symbols-outlined text-on-primary/60 text-2xl">
                fingerprint
              </span>
              <input
                className="bg-transparent border-none outline-none w-full text-on-primary placeholder:text-on-primary/40 font-headline-md text-headline-md py-2 tracking-widest"
                placeholder="e.g. 1234500001"
                value={nid}
                onChange={(e) => setNid(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()}
              />
            </div>
            <button
              onClick={submit}
              className="bg-surface-container-lowest hover:opacity-90 text-primary px-8 py-4 rounded-xl font-label-md text-label-md transition-all active:scale-95 shadow-lg flex items-center gap-2"
            >
              <span className="material-symbols-outlined">person_search</span>
              SEARCH PATIENT
            </button>
          </div>
        </div>
      </section>

      {/* Recent patients + network status */}
      <section className="grid grid-cols-1 xl:grid-cols-12 gap-gutter">
        {/* Recent patients */}
        <div className="xl:col-span-8 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 flex flex-col overflow-hidden">
          <div className="p-6 border-b border-surface-container flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-primary">history</span>
              <h3 className="font-title-lg text-title-lg text-on-surface">
                Recent Patients
              </h3>
            </div>
          </div>
          {recents.length === 0 ? (
            <div className="p-8 text-center text-on-surface-variant">
              <span className="material-symbols-outlined text-[40px] opacity-40">
                person_off
              </span>
              <p className="mt-2 text-body-md">
                No recent patient activity yet. Search a NID above to begin.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-surface-container-low border-b border-surface-container">
                  <tr>
                    <th className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
                      Patient
                    </th>
                    <th className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
                      NID Number
                    </th>
                    <th className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
                      Last Access
                    </th>
                    <th className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider text-right">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container">
                  {recents.map((p) => (
                    <tr
                      key={p.nid}
                      className="hover:bg-surface-container-low transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                            {initials(p.name)}
                          </div>
                          <span className="font-label-md text-label-md text-on-surface">
                            {p.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-body-md text-body-md text-on-surface-variant tabular-nums">
                        {p.nid}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="font-label-md text-label-md text-on-surface">
                            {p.when ? new Date(p.when).toLocaleDateString() : "—"}
                          </span>
                          <span className="font-label-sm text-label-sm text-on-surface-variant">
                            {p.action}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => onSearch?.(p.nid)}
                          className="p-2 rounded-lg hover:bg-primary/10 text-primary transition-colors"
                          title="Open unified record"
                        >
                          <span className="material-symbols-outlined">open_in_new</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Network status */}
        <div className="xl:col-span-4 flex flex-col gap-gutter">
          <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/30">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
                Network Status
              </h3>
              <span className="px-2 py-0.5 rounded bg-ok/10 text-ok font-label-sm text-label-sm">
                LIVE
              </span>
            </div>
            <div className="space-y-3">
              {facilities.length === 0 ? (
                <p className="text-body-md text-on-surface-variant">
                  No connected facilities reported.
                </p>
              ) : (
                facilities.map((f) => (
                  <div
                    key={f.id || f.name}
                    className="flex items-center justify-between p-3 rounded-lg bg-surface-container-low"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-ok" />
                      <span className="font-label-md text-label-md text-on-surface">
                        {f.name}
                      </span>
                    </div>
                    <span className="font-label-sm text-label-sm text-on-surface-variant">
                      Online
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function StatTile({ icon, value, label, tone = "primary" }) {
  const ring =
    tone === "secondary"
      ? "bg-secondary/10 text-secondary"
      : "bg-primary/10 text-primary";
  return (
    <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm border border-outline-variant/30 flex flex-col gap-2 justify-center">
      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${ring}`}>
        <span className="material-symbols-outlined">{icon}</span>
      </div>
      <div className="font-headline-md text-headline-md text-on-surface tabular-nums leading-none">
        {value}
      </div>
      <div className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
        {label}
      </div>
    </div>
  );
}
