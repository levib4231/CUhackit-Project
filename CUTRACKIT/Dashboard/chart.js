// Ensure this matches your global setup
document.addEventListener('DOMContentLoaded', () => {
    fetchTrafficData();
});

async function fetchTrafficData() {
    try {
        const { data, error } = await supabaseClient
            .from('gym_traffic') 
            .select('day_of_week, visits');

        if (error) throw error;

        // If the table is empty, the chart won't render. 
        if (data && data.length > 0) {
            const trafficData = transformDataForChart(data);
            renderChart(trafficData);
        } else {
            document.getElementById("busyLabel").textContent = "No traffic data in database.";
        }
    } catch (error) {
        console.error('Error fetching traffic:', error.message);
    }
}

function transformDataForChart(data) {
    const daysOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const trafficObject = {};
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
    barGraph.innerHTML = ''; 

    const values = Object.values(trafficData);
    const maxTraffic = Math.max(...values);
    const busiestDay = Object.keys(trafficData).find(day => trafficData[day] === maxTraffic);

    Object.entries(trafficData).forEach(([day, value]) => {
        const bar = document.createElement("div");
        bar.classList.add("bar");

        // Set height - added a check to prevent division by zero
        const height = maxTraffic > 0 ? (value / maxTraffic) * 160 + 20 : 20;
        bar.style.height = `${height}px`;

        // Clemson Colors: Red for busiest, Orange for others
        bar.style.background = (day === busiestDay && value > 0) ? "#d10000" : "#F56600";

        const label = document.createElement("div");
        label.classList.add("day-label");
        label.textContent = day.substring(0, 3);

        bar.appendChild(label);
        barGraph.appendChild(bar);
    });

    busyLabel.textContent = busiestDay ? `${busiestDay} is the busiest day` : "No traffic recorded.";
}