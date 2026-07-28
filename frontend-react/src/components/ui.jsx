// Small shared presentational primitives used across dashboards.

export function Card({ title, subtitle, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      {title && (
        <h2 className="font-headline-lg text-[24px] text-on-surface">{title}</h2>
      )}
      {subtitle && (
        <p className="text-body-md text-on-surface-variant mt-1 mb-4">
          {subtitle}
        </p>
      )}
      {children}
    </section>
  );
}

export function Field({ label, id, type = "text", value, onChange, placeholder }) {
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        type={type}
        className="field"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

const badgeTone = {
  ACTIVE: "bg-ok/10 text-ok",
  PENDING: "bg-warn/10 text-warn",
  REJECTED: "bg-error/10 text-error",
  src: "bg-primary/10 text-primary",
};

export function Badge({ children, tone = "src" }) {
  return (
    <span
      className={`inline-block px-2.5 py-0.5 rounded-full text-label-sm font-medium ${
        badgeTone[tone] || badgeTone.src
      }`}
    >
      {children}
    </span>
  );
}

export function Table({ head, children }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-outline-variant">
            {head.map((h) => (
              <th
                key={h}
                className="py-3 pr-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Stat({ value, label, tone = "primary" }) {
  const ring = tone === "secondary" ? "bg-secondary/10 text-secondary" : "bg-primary/10 text-primary";
  return (
    <div className="flex items-center gap-stack-md p-stack-lg bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant">
      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${ring}`}>
        <span className="material-symbols-outlined">insights</span>
      </div>
      <div>
        <div className="font-display-lg text-[28px] text-on-surface tabular-nums">
          {value}
        </div>
        <div className="font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">
          {label}
        </div>
      </div>
    </div>
  );
}
