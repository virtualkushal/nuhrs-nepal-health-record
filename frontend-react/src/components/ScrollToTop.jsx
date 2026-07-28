import { useEffect } from "react";
import { useLocation } from "react-router-dom";

// Resets scroll to the top whenever the route path changes.
// Fixes the SPA behavior where the browser keeps the previous scroll position.
export default function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" in window ? "instant" : "auto" });
  }, [pathname]);
  return null;
}
