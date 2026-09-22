/* =========================
   DEMO QUEUE DATA
========================= */

/*
    These numbers are temporary.

    Later FastAPI will send this
    information from PostgreSQL.
*/

const queueData = {

    dean: {
        count: 4,
        time: "10:35 AM"
    },

    printing: {
        count: 11,
        time: "11:20 AM"
    },

    cafe: {
        count: 7,
        time: "9:00–9:05 AM"
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


    badge.textContent = status.text;

    badge.classList.add(
        status.className
    );

    count.textContent = data.count;

    time.textContent = data.time;


    /* ---------- Navbar ---------- */

    const navStatus = document.getElementById(
        `${service}-nav-status`
    );

    navStatus.textContent = status.text;


    /* ---------- Navbar dot ---------- */

    const navDot = document.querySelector(
        `.${service}-dot`
    );

    navDot.classList.add(
        status.className
    );

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


/* =========================
   DEMO QUEUE UPDATE
========================= */

/*
    For now, we simulate a changing queue.

    Later this will be replaced by
    API calls to FastAPI.
*/

setInterval(() => {

    /*
        Small demo change.
        Don't use this in the final
        connected version.
    */

    queueData.cafe.count =
        Math.max(
            0,
            queueData.cafe.count +
            (Math.random() > 0.5 ? 1 : -1)
        );


    updateService("cafe");

}, 10000);