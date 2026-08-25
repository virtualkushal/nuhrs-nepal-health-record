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

export function Field({
  label,
  id,
  type = "text",
  value,
  onChange,
  placeholder,
  pattern,
  title,
  maxLength,
  inputMode,
  autoComplete,
  error,
}) {
  const errorId = error ? `${id}-error` : undefined;
  return (
    <div>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        type={type}
        className={`field ${error ? "field-error" : ""}`}
        value={value}
        placeholder={placeholder}
        pattern={pattern}
        title={title}
        maxLength={maxLength}
        inputMode={inputMode}
        autoComplete={autoComplete}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={errorId}
        onChange={(e) => onChange(e.target.value)}
      />
      <FieldError id={errorId}>{error}</FieldError>
    </div>
  );
}

// Inline error message shown beneath a single input. Rendered by <Field>, but
// also exported for raw inputs/selects that don't go through <Field> (e.g. the
// organization-type <select> on RegisterOrg). Renders nothing when empty.
export function FieldError({ id, children }) {
  if (!children) return null;
  return (
    <p id={id} role="alert" className="mt-1.5 text-label-sm text-error">
      {children}
    </p>
  );
}

// Persistent, top-of-form summary for general / non-field errors (auth failures,
// permission denials, cross-field validation). Unlike the transient toast, it
// stays until the next submit so the user can read and act on it. Renders
// nothing when there's no message.
export function FormBanner({ message }) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className="flex items-start gap-2 rounded-lg border border-error/20 bg-error/10 px-4 py-3 text-body-sm text-error"
    >
      <span className="material-symbols-outlined text-[18px] leading-5">
        error
      </span>
      <span className="flex-1">{message}</span>
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
