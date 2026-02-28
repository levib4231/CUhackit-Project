// Initialization
const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

let teams = []; 
let currentFilter = "all";
let currentSearch = "";
let currentSort = "default";
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

// Initial load from Supabase
document.addEventListener('DOMContentLoaded', fetchTeams);

// Search listener
if (searchInput) {
    searchInput.addEventListener("input", () => {
        currentSearch = searchInput.value;
        renderTeams();
    });
}

async function fetchTeams() {
    try {
        console.log("Fetching live teams and member counts...");
        // Fetch teams and count related memberships in one go
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

// Handle closing the modal
closeModal.addEventListener("click", () => {
    teamModal.style.display = "none";
});

window.addEventListener("click", (event) => {
    if (event.target === teamModal) {
        teamModal.style.display = "none";
    }
});

// Join Team Logic
modalJoinBtn.addEventListener("click", async () => {
    try {
        const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
        if (authError || !user) throw new Error("You must be logged in to join a team.");

        // Check if already a member
        const { data: existing } = await supabaseClient
            .from('Memberships')
            .select('*')
            .eq('team_id', selectedTeam.id)
            .eq('user_id', user.id)
            .single();

        if (existing) throw new Error("You are already in this team!");

        // Insert into Memberships
        const { error: joinError } = await supabaseClient
            .from('Memberships')
            .insert([{ 
                team_id: selectedTeam.id, 
                user_id: user.id 
            }]);

        if (joinError) throw joinError;

        alert(`Successfully joined ${selectedTeam.name}!`);

        // Refresh UI
        await fetchTeams(); 
        teamModal.style.display = "none";        

    } catch (err) {
        alert(err.message);
    }
});

function renderTeams() {
    teamGrid.innerHTML = "";

    let filtered = teams.filter(team => {
        const name = team.name || "";
        const matchesFilter = (currentFilter === "all" || team.team_size === currentFilter);
        const matchesSearch = name.toLowerCase().includes(currentSearch.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    if (filtered.length === 0) {
        teamGrid.innerHTML = "<p>No teams found matching your criteria.</p>";
        return;
    }

    filtered.forEach(team => {
        const card = document.createElement("div");
        card.classList.add("team-card");

        const memberCount = team.Memberships?.[0]?.count || 0;
        const shortDesc = team.description ? team.description.substring(0, 60) + "..." : "No description.";

        card.innerHTML = `
            <h3>${team.name || "Unnamed Team"}</h3>
            <p><strong>Size:</strong> ${team.team_size}</p>
            <p><strong>Members:</strong> ${memberCount}</p> 
            <p class="card-desc">${shortDesc}</p>
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
    
    // Set basic text
    modalTeamName.textContent = team.name || "Unnamed Team";
    modalTeamSize.textContent = `Team Size: ${team.team_size}`;
    modalTeamMembers.textContent = `Current Members: ${team.memberCount || 0}`;
    modalTeamDescription.textContent = team.description || "No description provided.";

    // Check if user is already a member to disable button
    const { data: { user } } = await supabaseClient.auth.getUser();
    const { data: isMember } = await supabaseClient
        .from('Memberships')
        .select('*')
        .eq('team_id', team.id)
        .eq('user_id', user?.id)
        .single();

    if (isMember) {
        modalJoinBtn.textContent = "Already a Member";
        modalJoinBtn.disabled = true;
        modalJoinBtn.style.opacity = "0.5";
    } else {
        modalJoinBtn.textContent = "Join Team";
        modalJoinBtn.disabled = false;
        modalJoinBtn.style.opacity = "1";
    }

    teamModal.style.display = "flex";
}