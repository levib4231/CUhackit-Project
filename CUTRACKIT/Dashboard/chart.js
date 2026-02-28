<<<<<<< HEAD
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
        bar.style.background = "#F56600";
    }

    // Add day label
    const label = document.createElement("div");
    label.classList.add("day-label");
    label.textContent = day.substring(0, 3);

    bar.appendChild(label);
    barGraph.appendChild(bar);
=======
document.addEventListener('DOMContentLoaded', () => {
    fetchTrafficData();
>>>>>>> a30ed61b53737f7496c40163e67bccdd3da11886
});

async function fetchTrafficData() {
    try {
        // Use your Supabase instance instead of a local fetch
        const { data, error } = await supabaseClient
            .from('gym_traffic') // Ensure this table exists in Supabase
            .select('day_of_week, visits');

        if (error) throw error;

        if (data && data.length > 0) {
            const trafficData = transformDataForChart(data);
            renderChart(trafficData);
        } else {
            console.warn("No traffic data found in Supabase.");
            document.getElementById("busyLabel").textContent = "No data recorded yet.";
        }
    } catch (error) {
        console.error('Error fetching utilization data:', error.message);
    }
}function transformDataForChart(data) {
    const daysOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const trafficObject = {};

    // Initialize all days to zero so the graph doesn't have holes
    daysOrder.forEach(day => trafficObject[day] = 0);

    data.forEach(item => {
        if (trafficObject.hasOwnProperty(item.day_of_week)) {
            trafficObject[item.day_of_week] = item.visits;
        }
    });

    return trafficObject;
}
function renderChart(trafficData) {
    const barGraph = document.getElementById("barGraph");
    const busyLabel = document.getElementById("busyLabel");

    // Clear any existing bars
    barGraph.innerHTML = ''; 

    if (Object.keys(trafficData).length === 0) return;

    // Find busiest day
    const maxTraffic = Math.max(...Object.values(trafficData));
    const busiestDay = Object.keys(trafficData).find(day => trafficData[day] === maxTraffic);

    // Build bars dynamically
    Object.entries(trafficData).forEach(([day, value]) => {
        const bar = document.createElement("div");
        bar.classList.add("bar");

        // Height scaling (max 180px, min 20px)
        bar.style.height = `${(value / maxTraffic) * 160 + 20}px`;

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
    if (busiestDay) {
        busyLabel.textContent = `${busiestDay} is the busiest day`;
    } else {
        busyLabel.textContent = 'No traffic data available.';
    }
}
