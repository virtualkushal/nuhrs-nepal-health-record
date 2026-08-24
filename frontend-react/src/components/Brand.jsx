import { useState } from "react";
import logo from "../assects/logo.png";

// Brand mark. Uses /logo.png from the public folder; if the file is missing,
// it gracefully falls back to the Material "health_and_safety" glyph so the
// app never shows a broken image.
export default function Brand({ size = 32, showText = true, subtitle = false }) {
  const [broken, setBroken] = useState(false);

  return (
    <div className="flex items-center gap-stack-sm">
      {broken ? (
        <span
          className="material-symbols-outlined text-primary"
          style={{ fontSize: size }}
        >
          health_and_safety
        </span>
      ) : (
        <img
          src={logo}
          alt="NUHRS logo"
          onError={() => setBroken(true)}
          style={{ height: size, width: "auto" }}
          className="object-contain"
        />
      )}
      {showText && (
        <div className="leading-tight">
          <div className="font-headline-md text-headline-md text-primary tracking-tight">
            NUHRS
          </div>
          <div className="text-[11px] text-on-surface-variant -mt-0.5">
            Nepal Unified Health Record System
          </div>
        </div>
      )}
    </div>
  );
}
