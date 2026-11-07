// ==========================================
// INQ — Central API Configuration
// ==========================================

const INQ_CONFIG = {
    // When your Render backend is live, paste your Render URL here:
    // Example: "https://inq-backend.onrender.com"
    RENDER_BACKEND_URL: "",

    getApiUrl() {
        // If a Render URL is set, use it everywhere
        if (this.RENDER_BACKEND_URL && this.RENDER_BACKEND_URL.trim() !== "") {
            const clean = this.RENDER_BACKEND_URL.trim().replace(/\/+$/, "");
            return clean.endsWith("/api") ? clean : `${clean}/api`;
        }

        // Local development fallback
        if (window.location.protocol === "file:") {
            return "http://127.0.0.1:8000/api";
        }

        const host = window.location.hostname || "127.0.0.1";
        return `http://${host}:8000/api`;
    }
};

// Global API constant accessible to all scripts
window.INQ_API = INQ_CONFIG.getApiUrl();
