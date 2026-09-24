import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, ".", "");
  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api/v1": {
          target: environment.VITE_BACKEND_URL || "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
  };
});
