// Initialization
const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

let teams = []; 
let currentFilter = "all";
let currentSearch = "";
let selectedTeam = null;

// Grab the UI elements
const teamGrid = document.getElementById("teamGrid");
const teamModal = document.getElementById("teamModal");
const closeModal = document.getElementById("closeModal");
const modalTeamName = document.getElementById("modalTeamName");
const modalTeamSize = document.getElementById("modalTeamSize");
const modalTeamMembers = document.getElementById("modalTeamMembers");
const modalTeamDescription = document.getElementById("modalTeamDescription");
const modalJoinBtn = document.getElementById("modalJoinBtn");
const searchInput = document.getElementById("searchInput");
const filterBtns = document.querySelectorAll(".filter-btn");

// Initial load from Supabase
document.addEventListener('DOMContentLoaded', fetchTeams);

// --- Event Listeners ---

// Size Filters
filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        // Update active UI state
        document.querySelector(".filter-btn.active")?.classList.remove("active");
        btn.classList.add("active");

        // Set filter and re-render
        currentFilter = btn.getAttribute("data-size");
        renderTeams();
    });
});

// Search Bar
if (searchInput) {
    searchInput.addEventListener("input", () => {
        currentSearch = searchInput.value;
        renderTeams();
    });
}

// Modal Closing
closeModal.addEventListener("click", () => {
    teamModal.style.display = "none";
});

window.addEventListener("click", (event) => {
    if (event.target === teamModal) {
        teamModal.style.display = "none";
    }
});

// --- Core Functions ---

async function fetchTeams() {
    try {
        console.log("Fetching live teams and member counts");
        // Fetch teams and count related memberships in one trip
        const { data, error } = await supabaseClient
            .from('Teams')
            .select(`
                *,
                Memberships(count)
            `);

        if (error) throw error;
        
        teams = data;
        renderTeams();
    } catch (err) {
        console.error("Error loading teams:", err.message);
        teamGrid.innerHTML = `<p class="error">Failed to load teams: ${err.message}</p>`;
    }
}
function renderTeams() {
    teamGrid.innerHTML = "";

    let filtered = teams.filter(team => {
        const name = team.name || "";
        const teamSize = team.team_size || "";
        const matchesFilter = (currentFilter === "all" || teamSize === currentFilter);
        const matchesSearch = name.toLowerCase().includes(currentSearch.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    if (filtered.length === 0) {
        teamGrid.innerHTML = "<p class='no-results'>No teams found matching your criteria.</p>";
        return;
    }

    filtered.forEach(team => {
        const card = document.createElement("div");
        card.classList.add("team-card");

        const memberCount = team.Memberships?.[0]?.count || 0;
        
        // BETTER DESCRIPTION LOGIC: 
        // Only truncate and add dots if the text is longer than 60 chars
        let displayDesc = team.description || "No description.";
        if (displayDesc.length > 60) {
            displayDesc = displayDesc.substring(0, 60).trim() + "...";
        }

        card.innerHTML = `
            <h3>${team.name || "Unnamed Team"}</h3>
            <p><strong>Size:</strong> ${team.team_size}</p>
            <p><strong>Members:</strong> ${memberCount}</p> 
            <p class="card-desc">${displayDesc}</p>
            <button class="view-btn">View Details</button>
        `;

        card.querySelector(".view-btn").addEventListener("click", () => {
            selectedTeam = { ...team, memberCount }; 
            openModal(selectedTeam);
        });

        teamGrid.appendChild(card);
    });
}
async function openModal(team) {
    selectedTeam = team;
    
    // Set text content
    modalTeamName.textContent = team.name || "Unnamed Team";
    modalTeamSize.textContent = `Team Size: ${team.team_size}`;
    modalTeamMembers.textContent = `Current Members: ${team.memberCount || 0}`;
    modalTeamDescription.textContent = team.description || "No description provided.";

    // Check if user is already a member to manage the Join button
    const { data: { user } } = await supabaseClient.auth.getUser();
    
    // Check local data first for speed, then verify with DB if necessary
    const isMember = team.Memberships?.some(m => m.user_id === user?.id);

    if (isMember) {
        modalJoinBtn.textContent = "Already a Member";
        modalJoinBtn.disabled = true;
        modalJoinBtn.style.opacity = "0.5";
        modalJoinBtn.style.cursor = "not-allowed";
    } else {
        modalJoinBtn.textContent = "Join Team";
        modalJoinBtn.disabled = false;
        modalJoinBtn.style.opacity = "1";
        modalJoinBtn.style.cursor = "pointer";
    }

    teamModal.style.display = "flex";
}

// Join Team Logic
modalJoinBtn.addEventListener("click", async () => {
    try {
        const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
        if (authError || !user) throw new Error("You must be logged in to join a team.");

        // Database insert
        const { error: joinError } = await supabaseClient
            .from('Memberships')
            .insert([{ 
                team_id: selectedTeam.id, 
                user_id: user.id 
            }]);

        if (joinError) {
            if (joinError.code === '23505') throw new Error("You are already in this team!");
            throw joinError;
        }

        alert(`Successfully joined ${selectedTeam.name}!`);

        // Refresh UI and Close Modal
        await fetchTeams(); 
        teamModal.style.display = "none";        

    } catch (err) {
        alert(err.message);
    }
});