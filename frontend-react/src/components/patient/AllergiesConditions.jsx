import { extractAllergies, extractActiveConditions } from "../../lib/fhirUtils.js";
import { fmtDate } from "./util.js";

// Allergies and active conditions — the most safety-critical at-a-glance info
// a patient should see. Both are real FHIR resources (AllergyIntolerance and
// Condition with clinicalStatus = active). Shows "None recorded" honestly when
// the bundle contains none.

export default function AllergiesConditions({ bundle }) {
  const allergies = extractAllergies(bundle);
  const conditions = extractActiveConditions(bundle);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Allergies */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="material-symbols-outlined text-tertiary text-[20px]">emergency</span>
          <span className="font-headline-md text-[18px] text-on-surface">Allergies</span>
        </div>
        {allergies.length === 0 ? (
          <p className="text-body-md text-on-surface-variant">None recorded</p>
        ) : (
          <div className="space-y-2">
            {allergies.map((a, i) => {
              const substance =
                a.code?.coding?.[0]?.display ||
                a.code?.text ||
                "Unknown substance";
              const severity = a.reaction?.[0]?.severity || null;
              return (
                <div
                  key={i}
                  className="flex items-start justify-between gap-2 pb-2 border-b border-outline-variant/30 last:border-0 last:pb-0"
                >
                  <div className="flex-1">
                    <p className="font-label-md text-on-surface">{substance}</p>
                    {a.reaction?.[0]?.manifestation?.[0]?.text && (
                      <p className="text-label-sm text-on-surface-variant">
                        {a.reaction[0].manifestation[0].text}
                      </p>
                    )}
                  </div>
                  {severity && (
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-label-sm font-label-sm ${
                        severity === "severe"
                          ? "bg-error/10 text-error"
                          : severity === "moderate"
                          ? "bg-warn/10 text-warn"
                          : "bg-outline/10 text-on-surface-variant"
                      }`}
                    >
                      {severity}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Active Conditions */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="material-symbols-outlined text-primary text-[20px]">clinical_notes</span>
          <span className="font-headline-md text-[18px] text-on-surface">Active Conditions</span>
        </div>
        {conditions.length === 0 ? (
          <p className="text-body-md text-on-surface-variant">None recorded</p>
        ) : (
          <div className="space-y-2">
            {conditions.map((c, i) => {
              const name =
                c.code?.coding?.[0]?.display ||
                c.code?.text ||
                "Unknown condition";
              const onset = c.onsetDateTime || c.recordedDate;
              return (
                <div
                  key={i}
                  className="flex items-start justify-between gap-2 pb-2 border-b border-outline-variant/30 last:border-0 last:pb-0"
                >
                  <div className="flex-1">
                    <p className="font-label-md text-on-surface">{name}</p>
                    {onset && (
                      <p className="text-label-sm text-on-surface-variant">
                        Since {fmtDate(onset)}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
