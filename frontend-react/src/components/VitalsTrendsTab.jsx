import TrendsPanel from "./TrendsPanel.jsx";

// Thin wrapper: the existing cross-hospital TrendsPanel, unchanged, living
// inside its own tab. TrendsPanel consumes raw bundle entries.
export default function VitalsTrendsTab({ bundle }) {
  const entries = bundle?.entry || [];
  return (
    <div>
      <TrendsPanel entries={entries} />
    </div>
  );
}
