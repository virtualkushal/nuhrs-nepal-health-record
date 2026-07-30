/**
 * TrendChart — a tiny, dependency-free SVG line chart for plotting a single
 * lab test's values over time. Used on the doctor's clinical timeline to show
 * how a patient's Hemoglobin / WBC / Platelet results trend across visits.
 *
 * Props:
 *   points: [{ date: ISOString, value: number }]  (assumed already time-ordered)
 *   unit:   string  (e.g. "g/dL")
 *   label:  string  (e.g. "Hemoglobin")
 */
export default function TrendChart({ points = [], unit = "", label = "" }) {
  if (!points.length) {
    return (
      <div className="text-sm text-gray-400 italic py-6 text-center">
        No {label || "data"} recorded yet.
      </div>
    );
  }

  // A single point can't draw a line, so show it as a labelled dot + value.
  const width = 320;
  const height = 140;
  const padX = 36;
  const padY = 20;

  const values = points.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  // Avoid a zero-height range when all values are equal.
  const span = max - min || 1;

  const plotW = width - padX * 2;
  const plotH = height - padY * 2;

  const x = (i) =>
    points.length === 1
      ? padX + plotW / 2
      : padX + (i / (points.length - 1)) * plotW;
  const y = (v) => padY + plotH - ((v - min) / span) * plotH;

  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(p.value).toFixed(1)}`)
    .join(" ");

  const latest = points[points.length - 1];

  const fmtDate = (iso) => {
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      });
    } catch {
      return "";
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-surface-750 p-3">
      <div className="mb-1 flex items-baseline justify-between">
        <h4 className="text-sm font-semibold text-gray-700">{label}</h4>
        <span className="text-sm text-gray-500">
          Latest: <span className="font-semibold text-gray-800">{latest.value}</span> {unit}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        role="img"
        aria-label={`${label} trend chart`}
      >
        {/* min / max reference gridlines */}
        <line x1={padX} y1={padY} x2={width - padX} y2={padY} stroke="#f1f5f9" />
        <line
          x1={padX}
          y1={height - padY}
          x2={width - padX}
          y2={height - padY}
          stroke="#f1f5f9"
        />
        <text x={4} y={padY + 4} fontSize="9" fill="#94a3b8">
          {max}
        </text>
        <text x={4} y={height - padY + 4} fontSize="9" fill="#94a3b8">
          {min}
        </text>

        {/* the trend line */}
        {points.length > 1 && (
          <path d={linePath} fill="none" stroke="#2563eb" strokeWidth="2" />
        )}

        {/* data points */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={x(i)} cy={y(p.value)} r="3.5" fill="#2563eb" />
            <text
              x={x(i)}
              y={height - 4}
              fontSize="8"
              fill="#94a3b8"
              textAnchor="middle"
            >
              {fmtDate(p.date)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
