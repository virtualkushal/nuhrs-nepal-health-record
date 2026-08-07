import { useMemo } from "react";
import {
  extractAllergies,
  extractActiveConditions,
  extractMedications,
  extractEncounters,
  extractSources,
  latestVitalByName,
  groupLabReports,
  classifyValue,
} from "../lib/fhirUtils.js";

// The default "Clinical Summary" tab: a fixed-height triage grid. Every card
// caps its items (3, or 2 for encounters) so the summary never grows into the
// long, messy scroll the old single timeline produced.

function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  if (Number.isNaN(dt.getTime())) return d;
  return dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

const TONE_DOT = { ok: "bg-ok", warn: "bg-warn", error: "bg-error" };
const TONE_TEXT = { ok: "text-ok", warn: "text-warn", error: "text-error" };

function SectionCard({ title, icon, action, children, className = "" }) {
  return (
    <div className={`bg-surface-container-lowest rounded-lg shadow-sm border border-outline-variant/30 p-6 flex flex-col ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-on-surface">
          {icon && <span className="material-symbols-outlined text-primary text-[20px]">{icon}</span>}
          <h3 className="font-title-lg text-title-lg">{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

function SourceTag({ source }) {
  if (!source) return null;
  return (
    <span className="inline-flex items-center gap-1 text-label-sm text-on-surface-variant">
      <span className="material-symbols-outlined text-[13px]">domain</span>
      {source}
    </span>
  );
}

function MoreLink({ label, onClick }) {
  return (
    <button onClick={onClick} className="text-primary font-label-sm text-label-sm hover:underline inline-flex items-center gap-1">
      {label}
      <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
    </button>
  );
}

// --- Critical Alerts: allergies + severe active conditions -----------------
function CriticalAlerts({ allergies, conditions }) {
  const severe = conditions.filter((c) =>
    /diabet|hypertens|cardiac|failure|malignan|cancer/i.test(c.code?.text || "")
  );
  if (allergies.length === 0 && severe.length === 0) return null;
  return (
    <div className="md:col-span-12 bg-error/10 border border-error/40 rounded-lg p-5">
      <div className="flex items-center gap-2 text-error mb-3">
        <span className="material-symbols-outlined">emergency_home</span>
        <h3 className="font-title-lg text-title-lg">Critical Alerts</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {allergies.map((a, i) => {
          const sev = a.reaction?.[0]?.severity;
          return (
            <span key={`a-${i}`} className="inline-flex items-center gap-1.5 bg-error text-on-error px-3 py-1.5 rounded-full font-label-md text-label-md">
              <span className="material-symbols-outlined text-[16px]">warning</span>
              {a.code?.text || "Allergen"}
              {sev && <span className="opacity-80 capitalize">· {sev}</span>}
            </span>
          );
        })}
        {severe.map((c, i) => (
          <span key={`c-${i}`} className="inline-flex items-center gap-1.5 bg-error/15 text-error border border-error/30 px-3 py-1.5 rounded-full font-label-md text-label-md">
            <span className="material-symbols-outlined text-[16px]">monitor_heart</span>
            {c.code?.text}
          </span>
        ))}
      </div>
    </div>
  );
}

// --- Recent Vitals: 4 tiles with Normal/Borderline/High dot ----------------
function VitalTile({ label, value, unit, tone }) {
  return (
    <div className="bg-surface-container-low rounded-lg p-4 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{label}</span>
        {tone && <span className={`w-2.5 h-2.5 rounded-full ${TONE_DOT[tone]}`} />}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="font-headline-md text-headline-md text-on-surface tabular-nums">{value}</span>
        {unit && <span className="font-label-sm text-label-sm text-on-surface-variant">{unit}</span>}
      </div>
    </div>
  );
}
function RecentVitals({ bundle }) {
  const specs = [
    { key: "Systolic blood pressure", label: "Systolic BP", short: "systolic blood pressure" },
    { key: "Heart rate", label: "Heart Rate", short: "heart rate" },
    { key: "Oxygen saturation", label: "SpO₂", short: "oxygen saturation" },
    { key: "Body weight", label: "Weight", short: "weight" },
  ];
  const tiles = specs.map((s) => {
    const obs = latestVitalByName(bundle, s.key);
    const value = obs?.valueQuantity?.value;
    const { tone } = classifyValue(s.short, value);
    return {
      label: s.label,
      value: value ?? "—",
      unit: obs?.valueQuantity?.unit || "",
      tone,
    };
  });
  return (
    <SectionCard title="Recent Vitals" icon="vital_signs" className="md:col-span-12">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {tiles.map((t) => (
          <VitalTile key={t.label} {...t} />
        ))}
      </div>
    </SectionCard>
  );
}

// --- Active Conditions -----------------------------------------------------
function ActiveConditions({ conditions, onNavigate }) {
  return (
    <SectionCard
      title="Active Conditions"
      icon="coronavirus"
      className="md:col-span-6"
      action={conditions.length > 3 && <MoreLink label="Problem List" onClick={() => onNavigate("conditions")} />}
    >
      {conditions.length === 0 ? (
        <p className="text-body-md text-on-surface-variant">No active conditions on record.</p>
      ) : (
        <ul className="space-y-3">
          {conditions.slice(0, 3).map((c, i) => {
            const icd = c.code?.coding?.[0]?.code;
            return (
              <li key={i} className="flex items-start justify-between gap-3 border-l-4 border-error/60 pl-3">
                <div>
                  <div className="font-label-md text-label-md text-on-surface">{c.code?.text || "Condition"}</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    {icd && (
                      <span className="text-[11px] bg-surface-container-highest text-on-surface-variant px-1.5 py-0.5 rounded-full">
                        ICD-10: {icd}
                      </span>
                    )}
                    <SourceTag source={c._source} />
                  </div>
                </div>
                <span className="font-label-sm text-label-sm text-on-surface-variant whitespace-nowrap">
                  {fmtDate(c.onsetDateTime)}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </SectionCard>
  );
}

// --- Current Medications ---------------------------------------------------
function CurrentMedications({ medications, onNavigate }) {
  return (
    <SectionCard
      title="Current Medications"
      icon="medication"
      className="md:col-span-6"
      action={medications.length > 3 && <MoreLink label="View all" onClick={() => onNavigate("medications")} />}
    >
      {medications.length === 0 ? (
        <p className="text-body-md text-on-surface-variant">No medications on record.</p>
      ) : (
        <ul className="space-y-3">
          {medications.slice(0, 3).map((m, i) => (
            <li key={i} className="flex items-start justify-between gap-3">
              <div>
                <div className="font-label-md text-label-md text-on-surface">
                  {m.medicationCodeableConcept?.text || "Medication"}
                </div>
                <div className="font-body-md text-body-md text-on-surface-variant">
                  {m.dosageInstruction?.[0]?.text || "—"}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  {m.requester?.display && (
                    <span className="text-label-sm text-on-surface-variant">{m.requester.display}</span>
                  )}
                  <SourceTag source={m._source} />
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}
// --- Latest Lab Results (replaces the old BP Trends slot) ------------------
function LatestLabResults({ labGroups, onNavigate }) {
  const latest = labGroups[0];
  return (
    <SectionCard
      title="Latest Lab Results"
      icon="labs"
      className="md:col-span-6"
      action={labGroups.length > 0 && <MoreLink label="All Reports" onClick={() => onNavigate("labs")} />}
    >
      {!latest ? (
        <p className="text-body-md text-on-surface-variant">No lab reports available.</p>
      ) : (
        <>
          <div className="flex items-center justify-between mb-3">
            <span className="font-label-md text-label-md text-on-surface">
              {latest.report.code?.text || "Laboratory Panel"}
            </span>
            <span className="font-label-sm text-label-sm text-on-surface-variant">
              {fmtDate(latest.report.effectiveDateTime)}
            </span>
          </div>
          {latest.analytes.length === 0 ? (
            <p className="text-body-md text-on-surface-variant">
              {latest.report.conclusion || "No individual analytes reported."}
            </p>
          ) : (
            <ul className="space-y-2">
              {latest.analytes.slice(0, 4).map((o, i) => {
                const v = o.valueQuantity?.value ?? o.valueString;
                const { tone } = classifyValue(o.code?.text, o.valueQuantity?.value);
                return (
                  <li key={i} className="flex items-center justify-between gap-3 bg-surface-container-low rounded-lg px-3 py-2">
                    <span className="font-body-md text-body-md text-on-surface">{o.code?.text || "Analyte"}</span>
                    <span className={`font-label-md text-label-md tabular-nums ${tone ? TONE_TEXT[tone] : "text-on-surface"}`}>
                      {v ?? "—"} {o.valueQuantity?.unit || ""}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
          <div className="mt-3"><SourceTag source={latest.report._source} /></div>
        </>
      )}
    </SectionCard>
  );
}

// --- Recent Encounters -----------------------------------------------------
function RecentEncounters({ encounters, onNavigate }) {
  const sorted = [...encounters].sort(
    (a, z) => new Date(z.period?.start || 0) - new Date(a.period?.start || 0)
  );
  return (
    <SectionCard
      title="Recent Encounters"
      icon="medical_information"
      className="md:col-span-6"
      action={encounters.length > 2 && <MoreLink label="View all" onClick={() => onNavigate("encounters")} />}
    >
      {sorted.length === 0 ? (
        <p className="text-body-md text-on-surface-variant">No encounters on record.</p>
      ) : (
        <ul className="space-y-3">
          {sorted.slice(0, 2).map((e, i) => (
            <li key={i} className="border-l-4 border-primary/50 pl-3">
              <div className="flex items-center justify-between">
                <span className="font-label-md text-label-md text-on-surface">
                  {e.reasonCode?.[0]?.text || e.type?.[0]?.text || "Clinical Visit"}
                </span>
                <span className="font-label-sm text-label-sm text-on-surface-variant">{fmtDate(e.period?.start)}</span>
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                {e.participant?.[0]?.individual?.display && (
                  <span className="text-label-sm text-on-surface-variant">
                    {e.participant[0].individual.display}
                  </span>
                )}
                <SourceTag source={e.serviceProvider?.display || e._source} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

// --- Care Network ----------------------------------------------------------
function CareNetwork({ sources, encounters }) {
  const lastSeen = [...encounters].sort(
    (a, z) => new Date(z.period?.start || 0) - new Date(a.period?.start || 0)
  )[0];
  return (
    <SectionCard title="Care Network" icon="hub" className="md:col-span-12">
      <div className="flex flex-wrap gap-2 mb-3">
        {sources.length === 0 ? (
          <span className="text-body-md text-on-surface-variant">No sources reported.</span>
        ) : (
          sources.map((s) => (
            <span key={s} className="inline-flex items-center gap-1.5 bg-primary-container/10 text-primary px-3 py-1.5 rounded-full border border-primary-container/20 font-label-md text-label-md">
              <span className="material-symbols-outlined text-[16px]">account_balance</span>
              {s}
            </span>
          ))
        )}
      </div>
      {lastSeen && (
        <p className="font-label-sm text-label-sm text-on-surface-variant">
          Last seen: {fmtDate(lastSeen.period?.start)} · {lastSeen.serviceProvider?.display || lastSeen._source || "—"}
        </p>
      )}
    </SectionCard>
  );
}

// --- The tab ---------------------------------------------------------------
export default function SummaryTab({ bundle, onNavigate }) {
  const allergies = useMemo(() => extractAllergies(bundle), [bundle]);
  const conditions = useMemo(() => extractActiveConditions(bundle), [bundle]);
  const medications = useMemo(() => extractMedications(bundle), [bundle]);
  const encounters = useMemo(() => extractEncounters(bundle), [bundle]);
  const sources = useMemo(() => extractSources(bundle), [bundle]);
  const labGroups = useMemo(() => groupLabReports(bundle), [bundle]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
      <CriticalAlerts allergies={allergies} conditions={conditions} />
      <RecentVitals bundle={bundle} />
      <ActiveConditions conditions={conditions} onNavigate={onNavigate} />
      <CurrentMedications medications={medications} onNavigate={onNavigate} />
      <LatestLabResults labGroups={labGroups} onNavigate={onNavigate} />
      <RecentEncounters encounters={encounters} onNavigate={onNavigate} />
      <CareNetwork sources={sources} encounters={encounters} />
    </div>
  );
}
