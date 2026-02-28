// Initialization (ensure these variables are defined or imported)
const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

// Form elements
const nameInput = document.getElementById("teamName");
const sizeInput = document.getElementById("teamSize");
const descInput = document.getElementById("teamDescription");
const tagsInput = document.getElementById("teamTags");
const errorMsg = document.getElementById("errorMsg");

// ... (keep your live preview event listeners as they are) ...

// Create team in Supabase
document.getElementById("createTeamBtn").addEventListener("click", async () => {
    const name = nameInput.value.trim();
    const size = sizeInput.value;
    const desc = descInput.value.trim();
    const tags = tagsInput.value.trim();

    // 1. Validation
    if (!name) {
        showError("Team name cannot be empty.");
        return;
    }

    try {
        // 2. Get the current user session
        const { data: { user }, error: authError } = await supabaseClient.auth.getUser();

        if (authError || !user) {
            throw new Error("You must be signed in to create a team.");
        }

        // 3. Insert into Supabase 'Teams' table
        const { data, error: insertError } = await supabaseClient
            .from('Teams')
            .insert([
                {
                    name: name,
                    team_size: size,        // Matches the new 'team_size' column
                    description: desc,      // Matches the new 'description' column
                    tags: tags,             // Matches the new 'tags' column
                    coach_id: user.id
                }
            ]);

        if (insertError) {
            if (insertError.code === '23505') throw new Error("Team name already exists.");
            throw insertError;
        }

        // 4. Success handling
        errorMsg.textContent = "";
        successModal.style.display = "flex";

        // Clear form
        nameInput.value = "";
        descInput.value = "";
        tagsInput.value = "";

    } catch (err) {
        showError(err.message);
    }
});

function showError(msg) {
    errorMsg.style.color = "#ff4d4d";
    errorMsg.textContent = msg;
}