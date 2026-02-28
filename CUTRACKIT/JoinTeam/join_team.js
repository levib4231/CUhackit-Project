// Shared data model
let teams = JSON.parse(localStorage.getItem("teams")) || [
    { name: "Clemson Tigers", size: "5v5", members: 3, description: "Competitive 5v5 squad.", created: Date.now() },
    { name: "Orange Elite", size: "4v4", members: 2, description: "Looking for shooters.", created: Date.now() - 5000 },
    { name: "Upstate Warriors", size: "3v3", members: 1, description: "Fast-paced 3v3 team.", created: Date.now() - 10000 },
    { name: "Palmetto Squad", size: "2v2", members: 2, description: "Strong duo team.", created: Date.now() - 15000 },
    { name: "Solo Kings", size: "1v1", members: 0, description: "1v1 challengers.", created: Date.now() - 20000 }
];

const teamGrid = document.getElementById("teamGrid");
const filterBtns = document.querySelectorAll(".filter-btn");
const searchInput = document.getElementById("searchInput");
const sortSelect = document.getElementById("sortSelect");

// Modal elements
const modal = document.getElementById("teamModal");
const closeModal = document.getElementById("closeModal");
const modalTeamName = document.getElementById("modalTeamName");
const modalTeamSize = document.getElementById("modalTeamSize");
const modalTeamMembers = document.getElementById("modalTeamMembers");
const modalTeamDescription = document.getElementById("modalTeamDescription");
const modalJoinBtn = document.getElementById("modalJoinBtn");

let currentFilter = "all";
let currentSearch = "";
let currentSort = "default";
let selectedTeam = null;

// Render teams
function renderTeams() {
    teamGrid.innerHTML = "";

    let filtered = teams.filter(team => {
        return (currentFilter === "all" || team.size === currentFilter) &&
               team.name.toLowerCase().includes(currentSearch.toLowerCase());
    });

    if (currentSort === "most") filtered.sort((a,b) => b.members - a.members);
    if (currentSort === "least") filtered.sort((a,b) => a.members - b.members);
    if (currentSort === "newest") filtered.sort((a,b) => b.created - a.created);
    if (currentSort === "oldest") filtered.sort((a,b) => a.created - b.created);

    filtered.forEach(team => {
        const card = document.createElement("div");
        card.classList.add("team-card");

        card.innerHTML = `
            <h3>${team.name}</h3>
            <p>Size: ${team.size}</p>
            <p>Members: ${team.members}</p>
            <button class="view-btn">View Details</button>
        `;

        card.querySelector(".view-btn").addEventListener("click", () => openModal(team));

        teamGrid.appendChild(card);
    });
}

// Modal logic
function openModal(team) {
    selectedTeam = team;
    modalTeamName.textContent = team.name;
    modalTeamSize.textContent = `Team Size: ${team.size}`;
    modalTeamMembers.textContent = `Members: ${team.members}`;
    modalTeamDescription.textContent = team.description;
    modal.style.display = "flex";
}

closeModal.addEventListener("click", () => {
    modal.style.display = "none";
});

// Join team
modalJoinBtn.addEventListener("click", () => {
    selectedTeam.members++;
    saveTeams();
    renderTeams();
    modal.style.display = "none";
});

// Save to localStorage
function saveTeams() {
    localStorage.setItem("teams", JSON.stringify(teams));
}

// Filters
filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelector(".filter-btn.active").classList.remove("active");
        btn.classList.add("active");
        currentFilter = btn.dataset.size;
        renderTeams();
    });
});

// Search
searchInput.addEventListener("input", () => {
    currentSearch = searchInput.value;
    renderTeams();
});

// Sort
sortSelect.addEventListener("change", () => {
    currentSort = sortSelect.value;
    renderTeams();
});

// Initial load
renderTeams();
