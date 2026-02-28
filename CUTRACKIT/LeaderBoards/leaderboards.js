// Example player data (replace with real account data later)
let players = [
    { name: "Ja'Vien", games: 42 },
    { name: "Marcus Hill", games: 18 },
    { name: "Aiden Brooks", games: 27 },
    { name: "Jordan Smith", games: 55 },
    { name: "Trey Johnson", games: 12 },
    { name: "Caleb Rivers", games: 33 },
    { name: "Ethan Cole", games: 9 },
    { name: "Zion Walker", games: 61 },
    { name: "Darius Brown", games: 24 },
    { name: "Malik Carter", games: 48 }
];

const leaderboardBody = document.getElementById("leaderboardBody");
const searchInput = document.getElementById("searchInput");
const filterSelect = document.getElementById("filterSelect");

// Render leaderboard
function renderLeaderboard() {
    leaderboardBody.innerHTML = "";

    let filtered = [...players];

    // Search filter
    const search = searchInput.value.toLowerCase();
    filtered = filtered.filter(p => p.name.toLowerCase().includes(search));

    // Sort by games played (descending)
    filtered.sort((a, b) => b.games - a.games);

    // Top filters
    if (filterSelect.value === "top10") filtered = filtered.slice(0, 10);
    if (filterSelect.value === "top25") filtered = filtered.slice(0, 25);

    // Render rows
    filtered.forEach((player, index) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${player.name}</td>
            <td>${player.games}</td>
        `;

        leaderboardBody.appendChild(row);
    });
}

// Event listeners
searchInput.addEventListener("input", renderLeaderboard);
filterSelect.addEventListener("change", renderLeaderboard);

// Initial load
renderLeaderboard();
