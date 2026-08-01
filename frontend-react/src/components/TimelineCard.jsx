// A single timeline entry, styled after the Stitch "Grouped Clinical Records"
// design. Renders one FHIR resource (Encounter / Observation / Condition /
// DiagnosticReport) as a card hanging off the vertical timeline rail.

function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  if (Number.isNaN(dt.getTime())) return d;
  return dt.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function fmtTime(d) {
  if (!d) return null;
  const dt = new Date(d);
  if (Number.isNaN(dt.getTime())) return null;
  const t = dt.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
  return t;
}

// Card chrome: timeline dot + left-accented container.
function Shell({ children }) {
  return (
    <div className="relative pl-20 group">
      <div className="absolute left-[30px] top-6 w-4 h-4 rounded-full border-4 border-surface bg-primary shadow-sm z-10 group-hover:scale-125 transition-transform" />
      <div className="bg-surface-container-lowest rounded-lg shadow-md border-l-4 border-primary overflow-hidden transition-all hover:shadow-xl hover:-translate-y-0.5 border border-outline-variant/30">
        {children}
      </div>
    </div>
  );
}

function SourceFooter({ source, icon = "domain" }) {
  if (!source) return null;
  return (
    <div className="mt-6 pt-4 border-t border-outline-variant/30 flex items-center gap-1">
      <span className="material-symbols-outlined text-on-surface-variant text-[16px]">
        {icon}
      </span>
      <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-widest">
        Source: {source}
      </span>
    </div>
  );
}

function KindHeader({ icon, kind, color = "text-primary" }) {
  return (
    <div className={`flex items-center gap-2 mb-1 ${color}`}>
      <span className="material-symbols-outlined text-[18px]">{icon}</span>
      <span className="font-label-sm text-label-sm uppercase tracking-widest font-bold">
        {kind}
      </span>
    </div>
  );
}

export default function TimelineCard({ resource: r, source }) {
  const type = r.resourceType;
  const src = source || r._source;

  // --- Source unavailable -------------------------------------------------
  if (type === "OperationOutcome") {
    return (
      <div className="relative pl-20 group">
        <div className="absolute left-[30px] top-6 w-4 h-4 rounded-full border-4 border-surface bg-warn shadow-sm z-10" />
        <div className="bg-warn/5 rounded-lg shadow-md border-l-4 border-warn overflow-hidden border border-outline-variant/30">
          <div className="p-6">
            <KindHeader icon="cloud_off" kind="Source Unavailable" color="text-warn" />
            <div className="text-body-md text-on-surface-variant mt-1">
              {r.issue?.[0]?.diagnostics || "This source could not be reached."}
            </div>
            <SourceFooter source={src} icon="error" />
          </div>
        </div>
      </div>
    );
  }

  // --- Encounter ----------------------------------------------------------
  if (type === "Encounter") {
    const when = r.period?.start;
    const practitioner = r.participant?.[0]?.individual?.display;
    const facility = r.serviceProvider?.display || src;
    const reason = r.reasonCode?.[0]?.text || r.type?.[0]?.text || "Clinical Visit";
    return (
      <Shell>
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <KindHeader icon="medical_information" kind="Clinical Encounter" />
              <h2 className="font-headline-md text-headline-md text-on-surface">
                {reason}
              </h2>
            </div>
            <div className="text-right">
              <div className="font-label-md text-label-md text-on-surface">
                {fmtDate(when)}
              </div>
              {fmtTime(when) && (
                <div className="font-label-sm text-label-sm text-on-surface-variant">
                  {fmtTime(when)}
                </div>
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 bg-surface-container-low p-4 rounded-lg">
            <div className="flex gap-4 items-center">
              <div className="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center">
                <span className="material-symbols-outlined text-on-surface-variant">
                  person
                </span>
              </div>
              <div>
                <div className="font-label-sm text-label-sm text-on-surface-variant">
                  Practitioner
                </div>
                <div className="font-title-lg text-title-lg text-on-surface">
                  {practitioner || "—"}
                </div>
              </div>
            </div>
            <div className="flex gap-4 items-center sm:border-l border-outline-variant sm:pl-6">
              <div className="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center">
                <span className="material-symbols-outlined text-on-surface-variant">
                  location_on
                </span>
              </div>
              <div>
                <div className="font-label-sm text-label-sm text-on-surface-variant">
                  Facility
                </div>
                <div className="font-title-lg text-title-lg text-on-surface">
                  {facility || "—"}
                </div>
              </div>
            </div>
          </div>
          <SourceFooter source={src} icon="verified" />
        </div>
      </Shell>
    );
  }

  // --- Condition ----------------------------------------------------------
  if (type === "Condition") {
    const name = r.code?.text || "Condition";
    const icd = r.code?.coding?.[0]?.code;
    const onset = r.onsetDateTime;
    return (
      <Shell>
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <KindHeader icon="warning" kind="Condition: Active" color="text-secondary" />
            <div className="font-label-md text-label-md text-on-surface-variant">
              {onset ? `${fmtDate(onset)} (Dx)` : ""}
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-headline-md text-headline-md text-on-surface">
                {name}
              </h3>
              {icd && (
                <div className="flex gap-1 mt-1">
                  <span className="px-2 py-0.5 bg-surface-container-highest text-on-surface-variant text-[10px] rounded-full">
                    ICD-10: {icd}
                  </span>
                </div>
              )}
            </div>
            <span className="material-symbols-outlined text-secondary">error</span>
          </div>
          <SourceFooter source={src} icon="account_balance" />
        </div>
      </Shell>
    );
  }

  // --- Observation (vitals) ----------------------------------------------
  if (type === "Observation") {
    const name = r.code?.text || "Observation";
    const value = r.valueQuantity?.value ?? r.valueString ?? "—";
    const unit = r.valueQuantity?.unit || "";
    const when = r.effectiveDateTime;
    const interp = r.interpretation?.[0]?.text || r.interpretation?.[0]?.coding?.[0]?.code;
    let badge = null;
    if (interp) {
      const hi = /high|hh|abnormal|hyper/i.test(interp);
      badge = (
        <span
          className={`font-label-sm text-label-sm text-white px-2 py-1 rounded ${
            hi ? "bg-error" : "bg-ok"
          }`}
        >
          {interp}
        </span>
      );
    }
    return (
      <Shell>
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <KindHeader icon="vital_signs" kind="Observation: Vitals" />
            <div className="font-label-md text-label-md text-on-surface-variant">
              {fmtDate(when)}
            </div>
          </div>
          <div className="flex items-center justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-baseline gap-1">
                <span className="font-headline-lg text-[32px] text-on-surface">
                  {value}
                </span>
                <span className="font-label-md text-label-md text-on-surface-variant">
                  {unit}
                </span>
              </div>
              <div className="font-label-sm text-label-sm text-on-surface-variant uppercase mt-1">
                {name}
              </div>
            </div>
            {badge && <div className="flex flex-col items-end">{badge}</div>}
          </div>
          <SourceFooter source={src} />
        </div>
      </Shell>
    );
  }

  // --- DiagnosticReport (lab panel) --------------------------------------
  if (type === "DiagnosticReport") {
    const name = r.code?.text || "Laboratory Panel";
    const loinc = r.code?.coding?.[0]?.code;
    const when = r.effectiveDateTime;
    const results = r.contained || [];
    return (
      <Shell>
        <div className="p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <KindHeader icon="science" kind="Laboratory Panel" />
              <h2 className="font-headline-md text-headline-md text-on-surface">
                {name}
              </h2>
            </div>
            <div className="text-right">
              <div className="font-label-md text-label-md text-on-surface">
                {fmtDate(when)}
              </div>
              {loinc && (
                <div className="px-4 py-0.5 bg-primary/10 text-primary font-label-sm text-label-sm rounded-full mt-1 inline-block">
                  LOINC: {loinc}
                </div>
              )}
            </div>
          </div>
          <div className="space-y-2">
            {results.length === 0 && (
              <p className="text-body-md text-on-surface-variant">
                {r.conclusion || "No individual analytes reported."}
              </p>
            )}
            {results.map((o, i) => {
              const analyte = o.code?.text || "Analyte";
              const v = o.valueQuantity?.value;
              const u = o.valueQuantity?.unit || "";
              const range = o.referenceRange?.[0]?.text;
              const flag = o.interpretation?.[0]?.text || o.interpretation?.[0]?.coding?.[0]?.code;
              const high = flag && /high|hh|abnormal/i.test(flag);
              return (
                <div
                  key={i}
                  className="grid grid-cols-12 gap-4 p-4 bg-surface-container-low rounded-lg items-center border border-outline-variant/20"
                >
                  <div className="col-span-6 sm:col-span-5">
                    <div className="font-label-md text-label-md text-on-surface font-bold">
                      {analyte}
                    </div>
                    {range && (
                      <div className="text-[12px] text-on-surface-variant">
                        Ref: {range}
                      </div>
                    )}
                  </div>
                  <div className="col-span-4 sm:col-span-4 text-center">
                    <div
                      className={`text-xl font-headline-md ${
                        high ? "text-secondary" : "text-on-surface"
                      }`}
                    >
                      {v ?? "—"}{" "}
                      <span className="text-label-sm text-on-surface-variant">
                        {u}
                      </span>
                    </div>
                    {flag && (
                      <div
                        className={`text-[10px] font-bold uppercase tracking-tighter ${
                          high ? "text-secondary" : "text-primary"
                        }`}
                      >
                        {flag}
                      </div>
                    )}
                  </div>
                  <div className="col-span-2 sm:col-span-3 text-right">
                    <span
                      className={`material-symbols-outlined ${
                        high ? "text-secondary" : "text-primary"
                      }`}
                    >
                      {high ? "trending_up" : "check_circle"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
          <SourceFooter source={src} icon="biotech" />
        </div>
      </Shell>
    );
  }

  // --- Fallback for any other resource type ------------------------------
  return (
    <Shell>
      <div className="p-6">
        <KindHeader icon="description" kind={type || "Record"} />
        <div className="text-body-md text-on-surface-variant mt-1">
          {r.code?.text || r.text?.div || "Clinical record"}
        </div>
        <SourceFooter source={src} />
      </div>
    </Shell>
  );
}
