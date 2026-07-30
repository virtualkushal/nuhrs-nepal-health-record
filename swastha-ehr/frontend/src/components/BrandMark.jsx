import { HeartPulse } from "lucide-react";

// Reusable SwasthyaEHR brand lockup. `variant="light"` renders white text for
// use on dark/gradient backgrounds; the default is for light backgrounds.
export default function BrandMark({ variant = "dark", subtitle }) {
  const light = variant === "light";
  return (
    <div className="flex items-center gap-3">
      <div
        className={
          light
            ? "p-2 rounded-xl bg-surface-750/20 backdrop-blur"
            : "p-2 rounded-xl bg-gradient-to-br from-teal-500 to-blue-600"
        }
      >
        <HeartPulse className="w-6 h-6 text-white" />
      </div>
      <div>
        <h1
          className={
            "text-xl font-bold tracking-tight " +
            (light ? "text-white" : "text-white")
          }
        >
          Swasthya<span className={light ? "text-teal-100" : "text-brand-400"}>EHR</span>
        </h1>
        {subtitle && (
          <p className={"text-sm " + (light ? "text-white/70" : "text-gray-400")}>
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
