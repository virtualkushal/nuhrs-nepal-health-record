// Base URL of the National Platform API.
// When served by the bundled nginx (docker compose), override at build/deploy
// time; for local dev the default points at the platform on localhost:8000.
window.NUHRS_CONFIG = {
  PLATFORM_API: (window.localStorage.getItem("nuhrs_api") || "http://localhost:8000") + "/api",
};
