import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../lib/api.js";
import { useToast } from "../../context/ToastContext.jsx";
import { Card } from "../../components/ui.jsx";
import TimelineCard from "../../components/TimelineCard.jsx";
import RecordFilters from "../../components/RecordFilters.jsx";
import PatientSummaryCard from "../../components/PatientSummaryCard.jsx";
import TrendsPanel from "../../components/TrendsPanel.jsx";

// Map a filter chip key to the FHIR resourceType(s) it should match.
const TYPE_MATCH = {
  ALL: () => true,
  Encounter: (t) => t === "Encounter",
  Observation: (t) => t === "Observation",
  DiagnosticReport: (t) => t === "DiagnosticReport",
  Condition: (t) => t === "Condition",
};

// Best-effort service date for a fetched FHIR resource (for grouping/sorting).
function resourceDate(r) {
  return (
    r.effectiveDateTime ||
    r.onsetDateTime ||
    r.period?.start ||
    r.issued ||
    null
  );
}

function yearOf(d) {
  if (!d) return "Undated";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? "Undated" : String(dt.getFullYear());
}

// Doctor / lab technician record exchange: search by NID, then fetch a unified,
// grouped, longitudinal clinical record (Stitch "Grouped Clinical Records").
export default function Exchange({ initialNid = "" }) {
  const { show } = useToast();
  const [nid, setNid] = useState(initialNid);
  const [result, setResult] = useState(null); // { patient, index }
  const [bundle, setBundle] = useState(null);
  const [searching, setSearching] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [activeType, setActiveType] = useState("ALL");
  const [activeSources, setActiveSources] = useState([]); // [] = show all

  async function search() {
    if (!nid.trim()) return;
    setSearching(true);
    setResult(null);
    setBundle(null);
    setError(null);
    setActiveType("ALL");
    try {
      const patient = await api.lookupPatient(nid.trim());
      const index = await api.patientIndex(nid.trim());
      setResult({ patient, index });
      // Default: all discovered sources enabled.
      const sources = [
        ...new Set(index.map((r) => r.organization_name).filter(Boolean)),
      ];
      setActiveSources(sources);
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

  function toggleSource(name) {
    setActiveSources((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]
    );
  }

  const sources = useMemo(
    () =>
      result
        ? [
            ...new Set(
              result.index.map((r) => r.organization_name).filter(Boolean)
            ),
          ]
        : [],
    [result]
  );

  // Entries from the fetched bundle, filtered by the active chips, grouped by year.
  const grouped = useMemo(() => {
    if (!bundle) return [];
    const entries = (bundle.entry || [])
      .map((e) => e.resource)
      .filter((r) => r && r.resourceType !== "Patient");

    const typeOk = TYPE_MATCH[activeType] || TYPE_MATCH.ALL;
    const filtered = entries.filter((r) => {
      if (r.resourceType === "OperationOutcome") return true; // always surface errors
      if (!typeOk(r.resourceType)) return false;
      if (activeSources.length > 0 && r._source && !activeSources.includes(r._source))
        return false;
      return true;
    });

    // Group by year, newest first.
    const byYear = new Map();
    for (const r of filtered) {
      const y = yearOf(resourceDate(r));
      if (!byYear.has(y)) byYear.set(y, []);
      byYear.get(y).push(r);
    }
    for (const list of byYear.values()) {
      list.sort((a, b) => new Date(resourceDate(b) || 0) - new Date(resourceDate(a) || 0));
    }
    return [...byYear.entries()].sort((a, b) => {
      if (a[0] === "Undated") return 1;
      if (b[0] === "Undated") return -1;
      return Number(b[0]) - Number(a[0]);
    });
  }, [bundle, activeType, activeSources]);

  const totalVisible = grouped.reduce((n, [, list]) => n + list.length, 0);

  // If we arrive with a pre-filled NID (e.g. from the Doctor Home quick search),
  // run the lookup automatically once.
  const autoRan = useRef(false);
  useEffect(() => {
    if (initialNid && !autoRan.current) {
      autoRan.current = true;
      search();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialNid]);

  return (
    <div className="space-y-stack-lg">
      {/* Search */}
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
            onKeyDown={(e) => e.key === "Enter" && search()}
          />
          <button
            onClick={search}
            disabled={searching}
            className="btn-primary ml-2 shrink-0"
          >
            {searching ? "Searching…" : "Search"}
          </button>
        </div>
      </Card>

      {error && (
        <Card>
          <p className="text-on-surface-variant">{error}</p>
        </Card>
      )}

      {result && (
        <>
          {/* Sync status banner */}
          <div className="bg-surface-container-low px-6 py-2 rounded-lg flex items-center justify-between border-l-4 border-primary">
            <div className="flex items-center gap-4 text-on-surface-variant">
              <span className="material-symbols-outlined text-primary">cloud_done</span>
              <span className="font-label-md text-label-md">
                {result.index.length} record(s) indexed across {sources.length}{" "}
                source{sources.length === 1 ? "" : "s"}.
              </span>
            </div>
            <span className="font-label-sm text-label-sm text-primary uppercase tracking-widest">
              {result.patient.full_name} · {result.patient.nid}
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left rail */}
            <aside className="lg:col-span-3 lg:sticky lg:top-24 flex flex-col gap-6">
              <RecordFilters
                index={result.index}
                activeType={activeType}
                onTypeChange={setActiveType}
                sources={sources}
                activeSources={activeSources}
                onToggleSource={toggleSource}
              />
              <PatientSummaryCard index={result.index} allergies={0} />
            </aside>

            {/* Main column */}
            <div className="lg:col-span-9 space-y-stack-lg">
              {/* Patient identity header */}
              <Card>
                <div className="flex items-start justify-between flex-wrap gap-4">
                  <div>
                    <h3 className="font-headline-lg text-[24px] text-on-surface">
                      {result.patient.full_name}{" "}
                      <span className="text-on-surface-variant text-body-md">
                        {result.patient.nid}
                      </span>
                    </h3>
                    <p className="text-on-surface-variant">
                      DOB {result.patient.date_of_birth} · {result.patient.gender}
                      {result.patient.phone ? ` · ${result.patient.phone}` : ""}
                    </p>
                  </div>
                  {!bundle && (
                    <button
                      onClick={fetchBundle}
                      disabled={fetching}
                      className="btn-primary"
                    >
                      {fetching
                        ? "Contacting facilities…"
                        : "Fetch full unified record"}
                    </button>
                  )}
                </div>
              </Card>

              {/* Before fetch: show the lightweight index preview */}
              {!bundle && (
                <Card>
                  <h4 className="font-headline-md text-headline-md text-on-surface mb-4">
                    Discoverable Records
                  </h4>
                  {result.index.length === 0 ? (
                    <p className="text-on-surface-variant">No records indexed.</p>
                  ) : (
                    <ul className="space-y-2">
                      {result.index.map((r, i) => (
                        <li
                          key={i}
                          className="flex items-center justify-between p-3 bg-surface-container-low rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-primary text-[18px]">
                              description
                            </span>
                            <span className="font-label-md text-label-md text-on-surface">
                              {r.resource_type}
                            </span>
                            <span className="text-body-md text-on-surface-variant">
                              {r.summary}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-on-surface-variant">
                            <span className="font-label-sm text-label-sm">
                              {r.organization_name}
                            </span>
                            <span className="font-label-sm text-label-sm">
                              {r.service_date}
                            </span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              )}

              {/* After fetch: cross-hospital trends + grouped timeline */}
              {bundle && (
                <>
                  <TrendsPanel entries={bundle.entry || []} />

                  <Card>
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="font-headline-lg text-[24px] text-on-surface">
                        Unified Clinical Record
                      </h3>
                      <span className="text-on-surface-variant text-body-md">
                        {totalVisible} of {bundle.total} resource(s)
                      </span>
                    </div>

                    {totalVisible === 0 ? (
                      <p className="text-on-surface-variant">
                        No records match the current filters.
                      </p>
                    ) : (
                      <div className="relative">
                        <div className="absolute left-8 top-0 bottom-0 w-px bg-outline-variant/30" />
                        <div className="flex flex-col gap-8">
                          {grouped.map(([year, list]) => (
                            <div key={year} className="flex flex-col gap-8">
                              <div className="relative flex items-center gap-6 -ml-2">
                                <div className="bg-primary text-on-primary font-label-md text-label-md px-4 py-1 rounded-full z-10 shadow-sm">
                                  {year}
                                </div>
                                <div className="h-px flex-1 bg-outline-variant/20" />
                              </div>
                              {list.map((r, i) => (
                                <TimelineCard
                                  key={`${year}-${i}`}
                                  resource={r}
                                  source={r._source}
                                />
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
