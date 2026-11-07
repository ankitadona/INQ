/* =========================
   DEMO QUEUE DATA
========================= */

/*
    These numbers serve as defaults/fallbacks.
    When the FastAPI backend is running, live data
    from PostgreSQL/SQLite updates them in real time.
*/

const queueData = {

    dean: {
        count: 0,
        time: "—"
    },

    printing: {
        count: 0,
        time: "—"
    },

    cafe: {
        count: 0,
        time: "—"
    }

};


/* =========================
   CROWD STATUS FUNCTION
========================= */

function getCrowdStatus(service, count) {

    if (service === "dean") {

        if (count <= 5) {
            return {
                text: "Low Crowd",
                className: "status-low"
            };
        }

        if (count <= 15) {
            return {
                text: "Moderate",
                className: "status-medium"
            };
        }

        return {
            text: "Highly Crowded",
            className: "status-high"
        };
    }


    if (service === "printing") {

        if (count <= 5) {
            return {
                text: "Low",
                className: "status-low"
            };
        }

        if (count <= 15) {
            return {
                text: "Busy",
                className: "status-medium"
            };
        }

        return {
            text: "Highly Crowded",
            className: "status-high"
        };
    }


    if (service === "cafe") {

        if (count <= 3) {
            return {
                text: "Low Crowd",
                className: "status-low"
            };
        }

        if (count <= 8) {
            return {
                text: "Moderate",
                className: "status-medium"
            };
        }

        return {
            text: "Highly Crowded",
            className: "status-high"
        };
    }

}


/* =========================
   UPDATE SERVICE
========================= */

function updateService(service) {

    const data = queueData[service];

    const status = getCrowdStatus(
        service,
        data.count
    );


    /* ---------- Card ---------- */

    const badge = document.getElementById(
        `${service}-badge`
    );

    const count = document.getElementById(
        `${service}-count`
    );

    const time = document.getElementById(
        `${service}-time`
    );

    if (badge && count && time) {
        badge.textContent = status.text;

        badge.className = "crowd-badge " + status.className;

        count.textContent = data.count;

        time.textContent = data.time;
    }


    /* ---------- Navbar ---------- */

    const navStatus = document.getElementById(
        `${service}-nav-status`
    );

    if (navStatus) {
        navStatus.textContent = status.text;
    }


    /* ---------- Navbar dot ---------- */

    const navDot = document.querySelector(
        `.${service}-dot`
    );

    if (navDot) {
        navDot.className = `nav-icon ${service}-dot ` + status.className;
    }

}


/* =========================
   UPDATE ALL SERVICES
========================= */

updateService("dean");

updateService("printing");

updateService("cafe");


/* =========================
   STATUS COLORS
========================= */

const style = document.createElement("style");

style.innerHTML = `

    .status-low {
        background: #ccefd9 !important;
        color: #176b39 !important;
    }

    .status-medium {
        background: #ffe0b5 !important;
        color: #9a5400 !important;
    }

    .status-high {
        background: #ffd0d0 !important;
        color: #a32323 !important;
    }

    .dean-dot.status-low,
    .printing-dot.status-low,
    .cafe-dot.status-low {
        background: #36a95d;
    }

    .dean-dot.status-medium,
    .printing-dot.status-medium,
    .cafe-dot.status-medium {
        background: #ed941f;
    }

    .dean-dot.status-high,
    .printing-dot.status-high,
    .cafe-dot.status-high {
        background: #d93636;
    }

`;

document.head.appendChild(style);


/* =========================
   HERO BUTTON
========================= */

const exploreButton =
    document.querySelector(".primary-button");

if (exploreButton) {
    exploreButton.addEventListener(
        "click",
        () => {

            document
                .querySelector(".services-section")
                .scrollIntoView({
                    behavior: "smooth"
                });

        }
    );
}


/* =========================
   FASTAPI LIVE INTEGRATION
========================= */

const API_BASE_URL = (function() {
    if (window.location.protocol === "file:") {
        return "http://127.0.0.1:8000/api";
    }
    const host = window.location.hostname || "127.0.0.1";
    return `http://${host}:8000/api`;
})();

let backendConnected = false;

async function fetchLiveQueueStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/queues/status`);
        if (!response.ok) return;

        const liveData = await response.json();
        backendConnected = true;

        if (liveData.dean) {
            queueData.dean.count = liveData.dean.count;
            queueData.dean.time = liveData.dean.estimated_time;
            updateService("dean");
        }

        if (liveData.printing) {
            queueData.printing.count = liveData.printing.count;
            queueData.printing.time = liveData.printing.estimated_time;
            updateService("printing");
        }

        if (liveData.cafe) {
            queueData.cafe.count = liveData.cafe.count;
            queueData.cafe.time = liveData.cafe.estimated_time;
            updateService("cafe");
        }

    } catch (err) {
        // Backend offline: retain current local queue state
        backendConnected = false;
    }
}

// Check for live updates every 5 seconds
fetchLiveQueueStatus();
setInterval(fetchLiveQueueStatus, 5000);
