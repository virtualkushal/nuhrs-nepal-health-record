import { useState } from "react";
import DoctorHome from "./DoctorHome.jsx";
import Exchange from "./Exchange.jsx";

// Wraps the doctor experience: a Home landing view whose central NID search
// hands off to the grouped-records Exchange view, with a way back Home.
export default function DoctorPortal() {
  const [view, setView] = useState("home"); // "home" | "records"
  const [nid, setNid] = useState("");

  if (view === "records") {
    return (
      <div className="space-y-stack-md">
        <button
          onClick={() => setView("home")}
          className="btn-ghost inline-flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          Back to Dashboard
        </button>
        <Exchange initialNid={nid} />
      </div>
    );
  }

  return (
    <DoctorHome
      onSearch={(value) => {
        setNid(value);
        setView("records");
      }}
    />
  );
}
