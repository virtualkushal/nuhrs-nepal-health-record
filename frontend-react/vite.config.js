import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Same-origin proxy so the httpOnly JWT cookies (SameSite=Lax) set by the
    // national backend are first-party. Everything under /api is forwarded to
    // the Django dev server; the SPA calls it via the relative "/api" base.
    //
    // changeOrigin is deliberately false: it preserves the browser's Host
    // (localhost:5173) so Django's CSRF origin check sees a matching
    // good_origin for cookie-authenticated writes. Flipping it to true would
    // make Django compute good_origin from the target host (127.0.0.1:8000)
    // and reject unsafe requests unless :5173 were in CSRF_TRUSTED_ORIGINS.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.js"],
  },
});
