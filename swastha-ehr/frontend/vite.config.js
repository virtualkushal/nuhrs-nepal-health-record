import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Frontend runs on port 3000. Any request to /api is proxied to the Django
// backend on port 8000, so the browser never hits a cross-origin issue during
// development and we can call the API with plain relative paths.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 3090,

    proxy: {

      "/api": {
        target: "http://127.0.0.1:8090",
        changeOrigin: true,
      },

    },
  },
});
