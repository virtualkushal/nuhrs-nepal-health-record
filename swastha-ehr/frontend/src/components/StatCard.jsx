// Small metric tile for the top of dashboards. `tone` picks an accent color.
const TONES = {
  slate: "bg-slate-500/10 text-slate-600",
  blue: "bg-blue-500/10 text-blue-600",
  emerald: "bg-emerald-500/10 text-emerald-600",
  violet: "bg-violet-500/10 text-violet-600",
  amber: "bg-amber-500/10 text-amber-600",
  teal: "bg-brand-500/10 text-brand-600",
  red: "bg-red-500/10 text-red-600",
};


export default function StatCard({ icon: Icon, label, value, tone = "slate" }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-outline-variant bg-surface-container-lowest p-4 shadow-sm">
      <div className={`rounded-xl p-2.5 ${TONES[tone] || TONES.slate}`}>
        {Icon && <Icon className="h-5 w-5" />}
      </div>
      <div>
        <p className="text-2xl font-bold leading-none text-on-surface">{value}</p>
        <p className="mt-1 text-xs font-medium uppercase tracking-wide text-on-surface-variant">
          {label}
        </p>
      </div>
    </div>
  );
}