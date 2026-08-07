import { latestVitalByName, classifyValue } from "../../lib/fhirUtils.js";
import { fmtDate, friendlyLabel, TONE_DOT, TONE_TEXT } from "./util.js";

// At-a-glance vital tiles from the mock. Each shows the latest single reading
// with a soft Normal/Watch/High dot from classifyValue(). `ref` must match a
// REFERENCE_RANGES key exactly; where none exists (e.g. weight) the chip is
// simply omitted rather than faked.

const SPECS = [
  { key: "Systolic blood pressure", label: "Blood Pressure", icon: "monitor_heart", ref: "systolic blood pressure" },
  { key: "Heart rate", label: "Heart Rate", icon: "cardiology", ref: "heart rate" },
  { key: "Oxygen saturation", label: "Oxygen (SpO₂)", icon: "pulmonology", ref: "oxygen saturation" },
  { key: "Body weight", label: "Weight", icon: "monitor_weight", ref: "body weight" },
];

function VitalCard({ spec, obs }) {
  const value = obs?.valueQuantity?.value;
  const unit = obs?.valueQuantity?.unit || "";
  const { label: cls, tone } = classifyValue(spec.ref, value);
  const friendly = friendlyLabel(cls);

  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="material-symbols-outlined text-primary text-[20px]">{spec.icon}</span>
        <span className="font-label-md text-label-md text-on-surface">{spec.label}</span>
      </div>

      {value == null ? (
        <p className="text-body-md text-on-surface-variant">No reading yet</p>
      ) : (
        <>
          <div className="flex items-baseline gap-1">
            <span className="font-display-lg text-[32px] text-on-surface tabular-nums">{value}</span>
            <span className="font-label-md text-label-md text-on-surface-variant">{unit}</span>
          </div>
          <div className="flex items-center justify-between mt-2 gap-2">
            {friendly ? (
              <span className={`inline-flex items-center gap-1.5 font-label-sm text-label-sm ${tone ? TONE_TEXT[tone] : "text-on-surface-variant"}`}>
                <span className={`w-2 h-2 rounded-full ${tone ? TONE_DOT[tone] : "bg-outline"}`} />
                {friendly}
              </span>
            ) : (
              <span />
            )}
            <span className="text-label-sm text-on-surface-variant whitespace-nowrap">
              {fmtDate(obs?.effectiveDateTime)}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

export default function VitalsCards({ bundle }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {SPECS.map((s) => (
        <VitalCard key={s.key} spec={s} obs={latestVitalByName(bundle, s.key)} />
      ))}
    </div>
  );
}
