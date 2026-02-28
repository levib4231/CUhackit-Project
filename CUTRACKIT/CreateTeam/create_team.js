// Load existing teams or create empty list
let teams = JSON.parse(localStorage.getItem("teams")) || [];

// Form elements
const nameInput = document.getElementById("teamName");
const sizeInput = document.getElementById("teamSize");
const descInput = document.getElementById("teamDescription");
const tagsInput = document.getElementById("teamTags");
const errorMsg = document.getElementById("errorMsg");

// Preview elements
const previewName = document.getElementById("previewName");
const previewSize = document.getElementById("previewSize");
const previewDesc = document.getElementById("previewDesc");
const previewTags = document.getElementById("previewTags");

// Modal
const successModal = document.getElementById("successModal");
const closeModal = document.getElementById("closeModal");

// Live preview updates
nameInput.addEventListener("input", () => {
    previewName.textContent = nameInput.value || "Team Name";
});

sizeInput.addEventListener("change", () => {
    previewSize.textContent = `Team Size: ${sizeInput.value}`;
});

descInput.addEventListener("input", () => {
    previewDesc.textContent = descInput.value || "Description will appear here.";
});

tagsInput.addEventListener("input", () => {
    previewTags.textContent = tagsInput.value ? `Tags: ${tagsInput.value}` : "";
});

// Create team
document.getElementById("createTeamBtn").addEventListener("click", () => {
    const name = nameInput.value.trim();
    const size = sizeInput.value;
    const desc = descInput.value.trim();
    const tags = tagsInput.value.trim();

    // Validation
    if (!name) {
        errorMsg.textContent = "Team name cannot be empty.";
        return;
    }

    if (teams.some(t => t.name.toLowerCase() === name.toLowerCase())) {
        errorMsg.textContent = "A team with this name already exists.";
        return;
    }

    // Create team object
    const newTeam = {
        name,
        size,
        members: 0,
        description: desc || "No description provided.",
        tags,
        created: Date.now()
    };

    // Save to localStorage
    teams.push(newTeam);
    localStorage.setItem("teams", JSON.stringify(teams));

    // Reset form
    nameInput.value = "";
    descInput.value = "";
    tagsInput.value = "";
    previewName.textContent = "Team Name";
    previewDesc.textContent = "Description will appear here.";
    previewTags.textContent = "";

    errorMsg.textContent = "";

    // Show success modal
    successModal.style.display = "flex";
});

// Close modal
closeModal.addEventListener("click", () => {
    successModal.style.display = "none";
});
