import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
// Proxy /api to the FastAPI port. Override if you run uvicorn on another port, e.g.:
//   VITE_DEV_API_PROXY=http://127.0.0.1:8001 npm run dev
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), "");
    var apiProxy = env.VITE_DEV_API_PROXY || env.VITE_API_PROXY || "http://127.0.0.1:8000";
    return {
        plugins: [react()],
        server: {
            host: "0.0.0.0",
            port: 5173,
            proxy: {
                "/api": apiProxy,
            },
        },
        build: {
            outDir: "dist",
            sourcemap: false,
        },
    };
});
