import { useEffect, useState } from "react";
import DoctorHome from "./DoctorHome.jsx";
import Exchange from "./Exchange.jsx";

// Wraps the doctor experience: a Home landing view whose central NID search
// hands off to the grouped-records Exchange view, with a way back Home.
export default function DoctorPortal() {
  const [view, setView] = useState("home"); // "home" | "records"
  const [nid, setNid] = useState("");

  // A doctor arriving via SwasthyaEHR single sign-on may bring a patient's
  // National ID with them. Consume it once and jump straight to that record.
  useEffect(() => {
    const ssoNid = window.sessionStorage.getItem("nuhrs_sso_nid");
    if (ssoNid) {
      window.sessionStorage.removeItem("nuhrs_sso_nid");
      setNid(ssoNid);
      setView("records");
    }
  }, []);

  if (view === "records") {
    return (
      <div className="space-y-stack-md">
        <button
          onClick={() => setView("home")}
          className="btn-ghost inline-flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-[18px]">
            arrow_back
          </span>
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
