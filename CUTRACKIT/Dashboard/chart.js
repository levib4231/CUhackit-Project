// Traffic data for each day (example numbers)
const trafficData = {
    Monday: 40,
    Tuesday: 55,
    Wednesday: 30,
    Thursday: 70,
    Friday: 167,
    Saturday: 90,
    Sunday: 50
};

const barGraph = document.getElementById("barGraph");
const busyLabel = document.getElementById("busyLabel");

// Find busiest day
const maxTraffic = Math.max(...Object.values(trafficData));
const busiestDay = Object.keys(trafficData).find(day => trafficData[day] === maxTraffic);

// Build bars dynamically
Object.entries(trafficData).forEach(([day, value]) => {
    const bar = document.createElement("div");
    bar.classList.add("bar");

    // Height scaling (max 200px)
    bar.style.height = `${(value / maxTraffic) * 180 + 20}px`;

    // Color busiest day red
    if (day === busiestDay) {
        bar.style.background = "#d10000";
    }

    // Add day label
    const label = document.createElement("div");
    label.classList.add("day-label");
    label.textContent = day.substring(0, 3);

    bar.appendChild(label);
    barGraph.appendChild(bar);
});

// Add busy label text
busyLabel.textContent = `${busiestDay} is the busiest day`;
