import { useMemo, useState } from "react";

/**
 * TrendsPanel — the cross-hospital longitudinal trends view.
 *
 * The core value of a *federated* record: the same clinical measurement
 * (e.g. Blood Pressure) may be recorded at several different facilities.
 * NUHRS aggregates every Observation of the same type — regardless of which
 * hospital/lab produced it — into ONE chart so a clinician sees the whole
 * trajectory, with each point tagged by its source organisation.
 *
 * Dependency-free: charts are hand-drawn SVG so we add no npm packages.
 */

// ---------------------------------------------------------------------------
// Reference ranges for common measurements (used to shade normal/high bands).
// Keyed by a normalised measurement name. Extend as needed.
// ---------------------------------------------------------------------------
const REFERENCE_RANGES = {
  "blood pressure": { low: 90, normalMax: 120, high: 140, unit: "mmHg" },
  "systolic blood pressure": { low: 90, normalMax: 120, high: 140, unit: "mmHg" },
  "blood glucose": { low: 70, normalMax: 100, high: 126, unit: "mg/dL" },
  glucose: { low: 70, normalMax: 100, high: 126, unit: "mg/dL" },
  hba1c: { low: 4, normalMax: 5.7, high: 6.5, unit: "%" },
  "ldl cholesterol": { low: 0, normalMax: 100, high: 130, unit: "mg/dL" },
  "total cholesterol": { low: 0, normalMax: 200, high: 240, unit: "mg/dL" },
  "heart rate": { low: 60, normalMax: 100, high: 120, unit: "bpm" },
  weight: { low: 0, normalMax: 0, high: 0, unit: "kg" },
  hemoglobin: { low: 12, normalMax: 17, high: 18, unit: "g/dL" },
};

// Distinct colours assigned per source organisation (stable within a render).
const SOURCE_COLORS = [
  "#007DCC", // primary blue
  "#D10056", // tertiary magenta
  "#00897B", // teal
  "#F9A825", // amber
  "#6A1B9A", // purple
  "#2E7D32", // green
];

// Pull the first numeric value out of a FHIR value that may be "130/85", "14.2", etc.
function numericValue(raw) {
  if (raw == null) return null;
  const match = String(raw).match(/-?\d+(\.\d+)?/);
  return match ? parseFloat(match[0]) : null;
}

function normaliseName(name) {
  return (name || "").trim().toLowerCase();
}

// Flatten every Observation out of the unified bundle, including those nested
// inside DiagnosticReport.contained (lab panels).
function extractObservations(entries) {
  const obs = [];
  for (const entry of entries) {
    const r = entry.resource || entry;
    if (!r) continue;
    if (r.resourceType === "Observation") {
      obs.push({
        name: r.code?.text || "Observation",
        value: numericValue(r.valueQuantity?.value),
        rawValue: r.valueQuantity?.value,
        unit: r.valueQuantity?.unit || "",
        date: r.effectiveDateTime || null,
        source: r._source || "Unknown source",
      });
    } else if (r.resourceType === "DiagnosticReport") {
      for (const c of r.contained || []) {
        if (c.resourceType === "Observation" || c.code) {
          obs.push({
            name: c.code?.text || "Lab result",
            value: numericValue(c.valueQuantity?.value),
            rawValue: c.valueQuantity?.value,
            unit: c.valueQuantity?.unit || "",
            date: c.effectiveDateTime || r.effectiveDateTime || null,
            source: r._source || "Unknown source",
          });
        }
      }
    }
  }
  return obs.filter((o) => o.value != null && !Number.isNaN(o.value));
}

// Group observations by normalised measurement name.
function groupByMeasurement(observations) {
  const groups = new Map();
  for (const o of observations) {
    const key = normaliseName(o.name);
    if (!groups.has(key)) groups.set(key, { name: o.name, points: [] });
    groups.get(key).points.push(o);
  }
  // Sort each series chronologically; keep only measurements with >= 2 points.
  for (const g of groups.values()) {
    g.points.sort((a, b) => new Date(a.date || 0) - new Date(b.date || 0));
  }
  return [...groups.values()];
}

function fmtDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  if (Number.isNaN(dt.getTime())) return d;
  return dt.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

// ---------------------------------------------------------------------------
// A single measurement's multi-source line chart (pure SVG).
// ---------------------------------------------------------------------------
function TrendChart({ group, sourceColor }) {
  const { name, points } = group;
  const W = 520;
  const H = 200;
  const padL = 44;
  const padR = 16;
  const padT = 16;
  const padB = 30;

  const values = points.map((p) => p.value);
  const times = points.map((p) => new Date(p.date || 0).getTime());
  const ref = REFERENCE_RANGES[normaliseName(name)];

  let minV = Math.min(...values);
  let maxV = Math.max(...values);
  if (ref && ref.high) {
    minV = Math.min(minV, ref.low);
    maxV = Math.max(maxV, ref.high);
  }
  // Pad the value axis a little.
  const span = maxV - minV || 1;
  minV -= span * 0.15;
  maxV += span * 0.15;

  const minT = Math.min(...times);
  const maxT = Math.max(...times);
  const tSpan = maxT - minT || 1;

  const x = (t) => padL + ((t - minT) / tSpan) * (W - padL - padR);
  const y = (v) => padT + (1 - (v - minV) / (maxV - minV)) * (H - padT - padB);

  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${x(times[i]).toFixed(1)} ${y(p.value).toFixed(1)}`)
    .join(" ");

  const latest = points[points.length - 1];
  const prev = points.length > 1 ? points[points.length - 2] : null;
  const delta = prev ? latest.value - prev.value : null;

  // Status of latest value vs reference range.
  let status = null;
  if (ref && ref.high) {
    if (latest.value >= ref.high) status = { label: "High", cls: "bg-error text-white" };
    else if (latest.value > ref.normalMax) status = { label: "Borderline", cls: "bg-warn/90 text-white" };
    else status = { label: "Normal", cls: "bg-ok/90 text-white" };
  }

  const unit = latest.unit || ref?.unit || "";
  const sources = [...new Set(points.map((p) => p.source))];

  return (
    <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant shadow-sm p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-title-lg text-title-lg text-on-surface capitalize">{name}</h4>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="font-display-lg text-[26px] tabular-nums text-on-surface">
              {latest.rawValue ?? latest.value}
            </span>
            <span className="text-body-md text-on-surface-variant">{unit}</span>
            {delta != null && (
              <span
                className={`text-label-sm font-medium ${
                  delta > 0 ? "text-error" : delta < 0 ? "text-ok" : "text-on-surface-variant"
                }`}
              >
                {delta > 0 ? "▲" : delta < 0 ? "▼" : "•"} {Math.abs(delta).toFixed(1)} since last
              </span>
            )}
          </div>
        </div>
        {status && (
          <span className={`px-2.5 py-1 rounded-full text-label-sm font-medium ${status.cls}`}>
            {status.label}
          </span>
        )}
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label={`${name} trend`}>
        {/* Reference bands */}
        {ref && ref.high && (
          <>
            <rect x={padL} y={y(ref.normalMax)} width={W - padL - padR} height={Math.max(0, y(ref.low) - y(ref.normalMax))} fill="#2E7D32" opacity="0.06" />
            <rect x={padL} y={y(ref.high)} width={W - padL - padR} height={Math.max(0, y(ref.normalMax) - y(ref.high))} fill="#F9A825" opacity="0.10" />
            <rect x={padL} y={padT} width={W - padL - padR} height={Math.max(0, y(ref.high) - padT)} fill="#D10056" opacity="0.07" />
            <line x1={padL} x2={W - padR} y1={y(ref.high)} y2={y(ref.high)} stroke="#D10056" strokeWidth="1" strokeDasharray="3 3" opacity="0.5" />
          </>
        )}

        {/* Axis baseline */}
        <line x1={padL} x2={W - padR} y1={H - padB} y2={H - padB} stroke="#c0c7d3" strokeWidth="1" />

        {/* Y axis labels (min / max) */}
        <text x={padL - 6} y={y(maxV) + 4} textAnchor="end" fontSize="10" fill="#707882">
          {maxV.toFixed(0)}
        </text>
        <text x={padL - 6} y={y(minV) + 4} textAnchor="end" fontSize="10" fill="#707882">
          {minV.toFixed(0)}
        </text>

        {/* The trend line */}
        <path d={linePath} fill="none" stroke="#007DCC" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

        {/* Data points coloured by source */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={x(times[i])} cy={y(p.value)} r="5" fill={sourceColor(p.source)} stroke="#fff" strokeWidth="1.5">
              <title>
                {`${p.rawValue ?? p.value} ${p.unit} · ${fmtDate(p.date)} · ${p.source}`}
              </title>
            </circle>
          </g>
        ))}

        {/* X axis first/last dates */}
        <text x={padL} y={H - padB + 18} fontSize="10" fill="#707882">
          {fmtDate(points[0].date)}
        </text>
        <text x={W - padR} y={H - padB + 18} textAnchor="end" fontSize="10" fill="#707882">
          {fmtDate(latest.date)}
        </text>
      </svg>

      {/* Per-source legend */}
      <div className="flex flex-wrap gap-3 mt-3">
        {sources.map((s) => (
          <span key={s} className="inline-flex items-center gap-1.5 text-label-sm text-on-surface-variant">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: sourceColor(s) }} />
            {s}
          </span>
        ))}
      </div>
      <p className="text-label-sm text-on-surface-variant mt-2">
        Aggregated across {sources.length} source{sources.length > 1 ? "s" : ""} via NUHRS · {points.length} readings
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// The panel: builds a stable source→colour map and lays out the charts.
// ---------------------------------------------------------------------------
export default function TrendsPanel({ entries }) {
  const [onlyMulti, setOnlyMulti] = useState(false);

  const groups = useMemo(() => {
    const obs = extractObservations(entries || []);
    return groupByMeasurement(obs);
  }, [entries]);

  const sourceColorMap = useMemo(() => {
    const map = new Map();
    let idx = 0;
    for (const g of groups) {
      for (const p of g.points) {
        if (!map.has(p.source)) {
          map.set(p.source, SOURCE_COLORS[idx % SOURCE_COLORS.length]);
          idx += 1;
        }
      }
    }
    return map;
  }, [groups]);

  const sourceColor = (s) => sourceColorMap.get(s) || "#707882";

  const visible = groups
    .filter((g) => g.points.length >= 2)
    .filter((g) => (onlyMulti ? new Set(g.points.map((p) => p.source)).size > 1 : true));

  if (groups.length === 0) return null;

  return (
    <section className="panel">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-headline-lg text-[24px] text-on-surface">Longitudinal Health Trends</h2>
          <p className="text-body-md text-on-surface-variant mt-1">
            The same measurement from every facility, plotted on one timeline.
          </p>
        </div>
        <label className="inline-flex items-center gap-2 text-label-md text-on-surface-variant cursor-pointer select-none">
          <input
            type="checkbox"
            checked={onlyMulti}
            onChange={(e) => setOnlyMulti(e.target.checked)}
            className="w-4 h-4 accent-primary"
          />
          Cross-hospital only
        </label>
      </div>

      {visible.length === 0 ? (
        <p className="text-on-surface-variant">
          Not enough repeated measurements to plot a trend yet.
        </p>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
          {visible.map((g) => (
            <TrendChart key={g.name} group={g} sourceColor={sourceColor} />
          ))}
        </div>
      )}
    </section>
  );
}
