// Small metric tile for the top of dashboards. `tone` picks an accent color.
const TONES = {
  slate: "bg-slate-500/20 text-slate-300",
  blue: "bg-blue-500/20 text-blue-300",
  emerald: "bg-emerald-500/20 text-emerald-300",
  violet: "bg-violet-500/20 text-violet-300",
  amber: "bg-amber-500/20 text-amber-300",
  teal: "bg-brand-500/20 text-brand-300",
  red: "bg-red-500/20 text-red-300",
};


export default function StatCard({ icon: Icon, label, value, tone = "slate" }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-line bg-surface-750 p-4 shadow-lg shadow-black/20">
      <div className={`rounded-xl p-2.5 ${TONES[tone] || TONES.slate}`}>
        {Icon && <Icon className="h-5 w-5" />}
      </div>
      <div>
        <p className="text-2xl font-bold leading-none text-white">{value}</p>
        <p className="mt-1 text-xs font-medium uppercase tracking-wide text-gray-400">
          {label}
        </p>
      </div>
    </div>
  );
}


