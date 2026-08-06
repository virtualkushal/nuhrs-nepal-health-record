import { useState } from "react";

// Sticky patient identity header for the doctor dashboard.
// Left: avatar + name + NID · age · sex. Center: inline NID search so the
// doctor can switch patients without returning to the Home landing view.
// Right: blood-group pill + allergy badge (red when the patient has any).

function ageFrom(dob) {
  if (!dob) return null;
  const d = new Date(dob);
  if (Number.isNaN(d.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - d.getFullYear();
  const m = now.getMonth() - d.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < d.getDate())) age -= 1;
  return age;
}

function initials(name = "") {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
}

export default function PatientHeader({
  patient,
  bloodGroup,
  allergyCount = 0,
  onSearch,
}) {
  const [nid, setNid] = useState("");
  const name = patient?.full_name || "Unknown patient";
  const age = ageFrom(patient?.date_of_birth);

  const meta = [
    patient?.nid && `NID ${patient.nid}`,
    age != null && `${age} yrs`,
    patient?.gender,
  ]
    .filter(Boolean)
    .join(" · ");

  function submit() {
    const clean = nid.replace(/\D/g, "");
    if (clean) onSearch?.(clean);
  }

  return (
    <div className="sticky top-20 z-20 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/30 px-6 py-4 flex flex-col lg:flex-row lg:items-center gap-4">
      {/* Identity */}
      <div className="flex items-center gap-4 min-w-0">
        <div className="w-14 h-14 rounded-full bg-primary/10 text-primary flex items-center justify-center font-headline-md text-headline-md shrink-0">
          {initials(name) || <span className="material-symbols-outlined">person</span>}
        </div>
        <div className="min-w-0">
          <h2 className="font-headline-lg text-[22px] text-on-surface truncate">
            {name}
          </h2>
          <p className="font-label-md text-label-md text-on-surface-variant truncate">
            {meta || "—"}
          </p>
        </div>
      </div>

      {/* Inline NID search */}
      <div className="flex-1 flex items-center bg-surface-container rounded-full px-4 py-1.5 border border-outline-variant lg:max-w-sm lg:mx-auto">
        <span className="material-symbols-outlined text-on-surface-variant mr-2 text-[20px]">
          fingerprint
        </span>
        <input
          className="bg-transparent border-none outline-none w-full text-on-surface font-body-md text-body-md"
          placeholder="Switch patient by NID…"
          value={nid}
          onChange={(e) => setNid(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        {nid && (
          <button
            onClick={submit}
            className="text-primary text-label-sm font-label-sm uppercase tracking-wider shrink-0"
          >
            Go
          </button>
        )}
      </div>

      {/* Safety chips */}
      <div className="flex items-center gap-2 shrink-0">
        {bloodGroup && (
          <span className="inline-flex items-center gap-1 bg-secondary-fixed text-on-secondary-fixed px-3 py-1.5 rounded-full font-label-md text-label-md">
            <span className="material-symbols-outlined text-[18px]">bloodtype</span>
            {bloodGroup}
          </span>
        )}
        {allergyCount > 0 ? (
          <span className="inline-flex items-center gap-1 bg-error text-on-error px-3 py-1.5 rounded-full font-label-md text-label-md">
            <span className="material-symbols-outlined text-[18px]">warning</span>
            {allergyCount} {allergyCount === 1 ? "Allergy" : "Allergies"}
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 bg-ok/10 text-ok px-3 py-1.5 rounded-full font-label-md text-label-md">
            <span className="material-symbols-outlined text-[18px]">check_circle</span>
            No allergies
          </span>
        )}
      </div>
    </div>
  );
}
