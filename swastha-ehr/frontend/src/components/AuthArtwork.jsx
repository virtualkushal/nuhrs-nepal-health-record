import { Building2, Stethoscope, Pill, User } from "lucide-react";
import BrandMark from "./BrandMark";

export default function AuthArtwork() {
  return (
    <div className="relative hidden lg:flex flex-col justify-between overflow-hidden bg-gradient-to-br from-teal-500 via-sky-500 to-blue-700 p-10 text-white">
      <style>{`
        @keyframes draw-path {
          from { stroke-dashoffset: 600; }
          to { stroke-dashoffset: 0; }
        }
        @keyframes node-in {
          from { opacity: 0; transform: translateY(6px) scale(0.9); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes pulse-dot {
          0%, 100% { box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.55); }
          50% { box-shadow: 0 0 0 8px rgba(251, 191, 36, 0); }
        }
        .path-draw { animation: draw-path 1.6s ease-out forwards; }
        .node-in { opacity: 0; animation: node-in 0.5s ease-out forwards; }
        .pulse-dot { animation: pulse-dot 2s ease-in-out 1.6s infinite; }
      `}</style>

      {/* soft decorative blobs */}
      <div className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-surface-750/10 blur-2xl" />
      <div className="pointer-events-none absolute bottom-0 -left-16 h-72 w-72 rounded-full bg-surface-750/10 blur-2xl" />

      <div className="relative z-10">
        <BrandMark variant="light" />
      </div>

      {/* center illustration: the record's path across the system */}
      <div className="relative z-10 flex flex-1 items-center justify-center">
        <div className="relative h-40 w-72">
          <svg
            viewBox="0 0 280 160"
            className="absolute inset-0 h-full w-full"
            fill="none"
          >
            <path
              d="M 30 100 C 70 40, 110 40, 140 80 S 210 130, 250 70"
              stroke="white"
              strokeOpacity="0.55"
              strokeWidth="2"
              strokeDasharray="6 6"
              strokeLinecap="round"
              className="path-draw"
              style={{ strokeDasharray: 600, strokeDashoffset: 600 }}
              pathLength={600}
            />
          </svg>

          {/* Clinic */}
          <div
            className="node-in absolute flex h-12 w-12 items-center justify-center rounded-full bg-surface-750/15 backdrop-blur"
            style={{ left: 6, top: 84, animationDelay: "0.2s" }}
          >
            <Building2 className="h-6 w-6 text-white" strokeWidth={1.75} />
          </div>

          {/* Doctor */}
          <div
            className="node-in absolute flex h-12 w-12 items-center justify-center rounded-full bg-surface-750/15 backdrop-blur"
            style={{ left: 92, top: 20, animationDelay: "0.55s" }}
          >
            <Stethoscope className="h-6 w-6 text-white" strokeWidth={1.75} />
          </div>

          {/* Pharmacy */}
          <div
            className="node-in absolute flex h-12 w-12 items-center justify-center rounded-full bg-surface-750/15 backdrop-blur"
            style={{ left: 162, top: 96, animationDelay: "0.9s" }}
          >
            <Pill className="h-6 w-6 text-white" strokeWidth={1.75} />
          </div>

          {/* Patient — journey's end, gets the accent */}
          <div
            className="node-in absolute flex h-14 w-14 items-center justify-center rounded-full bg-surface-750 shadow-lg"
            style={{ left: 222, top: 42, animationDelay: "1.25s" }}
          >
            <User className="h-7 w-7 text-blue-300" strokeWidth={1.75} />
            <span className="pulse-dot absolute -right-1 -top-1 h-3.5 w-3.5 rounded-full bg-amber-400" />
          </div>
        </div>
      </div>

      <div className="relative z-10 max-w-sm">
        <h2 className="text-2xl font-bold font-display leading-snug">
          Care that follows the patient.
        </h2>
        <p className="mt-2 text-white/80">
          A FHIR-enabled hospital record system built for Nepal's clinics.
        </p>
      </div>
    </div>
  );
}
