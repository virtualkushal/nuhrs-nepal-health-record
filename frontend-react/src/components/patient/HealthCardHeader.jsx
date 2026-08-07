import { fmtDate } from "./util.js";

// The patient's identity card — the "National Health Card" hero from the mock.
// A calm blue gradient with the Ministry framing, the identity facts as labeled
// mini-stats (NID · DOB/age · gender · blood group), and the record-export
// actions. Height/weight are deliberately NOT shown here: they are clinical
// vitals, not identity, and belong on the Vitals tiles — the card carries only
// what a national health ID card would.

function initials(name = "") {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
}

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

function Stat({ label, value }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wider opacity-70">{label}</div>
      <div className="font-label-md text-label-md">{value ?? "—"}</div>
    </div>
  );
}

export default function HealthCardHeader({ patient, bloodGroup, onDownloadPdf, onDownloadJson }) {
  const name = patient?.full_name || "—";
  const age = ageFrom(patient?.date_of_birth);

  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-primary-container text-on-primary shadow-lg shadow-primary/20">
      {/* soft decorative discs */}
      <div className="pointer-events-none absolute -top-16 -right-10 w-56 h-56 rounded-full bg-on-primary/10" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 w-72 h-72 rounded-full bg-on-primary/5" />

      <div className="relative p-6 sm:p-7">
        <div className="flex items-center justify-between gap-3 mb-5">
          <span className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-[0.18em] opacity-80">
            <span className="material-symbols-outlined text-[16px]">health_and_safety</span>
            NUHRS · National Health Card
          </span>
          {bloodGroup && (
            <span className="inline-flex items-center gap-1 bg-on-primary/15 px-3 py-1.5 rounded-full font-label-md text-label-md">
              <span className="material-symbols-outlined text-[18px]">bloodtype</span>
              {bloodGroup}
            </span>
          )}
        </div>

        <div className="flex flex-col sm:flex-row sm:items-end gap-5">
          <div className="w-16 h-16 rounded-2xl bg-on-primary/15 flex items-center justify-center font-headline-lg text-headline-md shrink-0">
            {initials(name) || <span className="material-symbols-outlined">person</span>}
          </div>

          <div className="min-w-0 flex-1">
            <h2 className="font-headline-xl text-[28px] leading-tight truncate">{name}</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-3 mt-4">
              <Stat label="National ID" value={patient?.nid} />
              <Stat
                label="Date of Birth"
                value={
                  patient?.date_of_birth
                    ? `${fmtDate(patient.date_of_birth)}${age != null ? ` · ${age} yrs` : ""}`
                    : null
                }
              />
              <Stat
                label="Gender"
                value={patient?.gender ? patient.gender.charAt(0) + patient.gender.slice(1).toLowerCase() : null}
              />
              <Stat label="Blood Group" value={bloodGroup} />
            </div>
          </div>
        </div>

        {(onDownloadPdf || onDownloadJson) && (
          <div className="flex flex-wrap items-center gap-3 mt-6">
            {onDownloadPdf && (
              <button
                onClick={onDownloadPdf}
                className="inline-flex items-center gap-1.5 bg-secondary-container text-on-secondary-container px-4 py-2 rounded-full font-label-md text-label-md hover:opacity-90 transition-opacity"
              >
                <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
                Save as PDF
              </button>
            )}
            {onDownloadJson && (
              <button
                onClick={onDownloadJson}
                className="inline-flex items-center gap-1.5 bg-on-primary/15 text-on-primary px-4 py-2 rounded-full font-label-md text-label-md hover:bg-on-primary/25 transition-colors"
              >
                <span className="material-symbols-outlined text-[18px]">data_object</span>
                Export data (JSON)
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
