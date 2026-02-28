console.log("Account JS running");
const BACKEND_URL = "http://127.0.0.1:5000"; // change when deployed

const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);


const nameInput = document.getElementById("nameInput");
const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");
const confirmPasswordInput = document.getElementById("confirmPasswordInput");
const saveBtn = document.getElementById("saveBtn");
const errorMsg = document.getElementById("errorMsg");

const previewName = document.getElementById("previewName");
const previewEmail = document.getElementById("previewEmail");
const previewPassword = document.getElementById("previewPassword");


// =====================================
// 🔥 FETCH PROFILE FROM BACKEND
// =====================================
document.addEventListener("DOMContentLoaded", async () => {
    // 1. Get the current authenticated user
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();

    if (authError || !user) {
        console.log("User not logged in.");
        // Optional: window.location.href = "../Login/login.html";
        return;
    }

    try {
        // 2. Fetch the corresponding row from the Profiles table using auth_id
        const { data: profile, error: profileError } = await supabaseClient
            .from('Profiles')
            .select('fname, lname, email')
            .eq('id', user.id)
            .maybeSingle();

        if (profileError) throw profileError;

        // 3. Fallback logic: Use Auth email if Profile email is missing
        const userEmail = profile?.email || user.email;
        const firstName = profile?.fname || "";
        const lastName = profile?.lname || "";
        const fullName = `${firstName} ${lastName}`.trim();

        // Fill form inputs
        nameInput.value = fullName || "User";
        emailInput.value = userEmail;

        // Update preview text
        previewName.textContent = fullName || "Your Name";
        previewEmail.textContent = userEmail || "your@email.com";

    } catch (error) {
        console.error("Profile fetch failed:", error.message);
        errorMsg.textContent = "Failed to load profile info.";
    }
});

// =====================================
// Save changes (Updated for Supabase)
// =====================================
saveBtn.addEventListener("click", async () => {
    const fullName = nameInput.value.trim();
    const email = emailInput.value.trim();
    const pass = passwordInput.value.trim();
    const confirm = confirmPasswordInput.value.trim();

    // Basic Validation
    if (!fullName || !email) {
        errorMsg.style.color = "red";
        errorMsg.textContent = "Name and email cannot be empty.";
        return;
    }

    // Split name back into fname/lname (basic split)
    const nameParts = fullName.split(" ");
    const fname = nameParts[0];
    const lname = nameParts.slice(1).join(" ") || "";

    try {
        const { data: { user } } = await supabaseClient.auth.getUser();

        // 1. Update Profiles table
        const { error: updateError } = await supabaseClient
            .from('Profiles')
            .update({ fname, lname, email })
            .eq('auth_id', user.id);

        if (updateError) throw updateError;

        // 2. Handle Password Change (Optional)
        if (pass) {
            if (pass !== confirm) {
                errorMsg.style.color = "red";
                errorMsg.textContent = "Passwords do not match.";
                return;
            }
            const { error: passError } = await supabaseClient.auth.updateUser({ password: pass });
            if (passError) throw passError;
        }

        errorMsg.style.color = "#00a651";
        errorMsg.textContent = "Profile updated successfully!";
    } catch (error) {
        errorMsg.style.color = "red";
        errorMsg.textContent = "Update failed: " + error.message;
    }
});
// =====================================
// Live preview updates (UNCHANGED)
// =====================================
nameInput.addEventListener("input", () => {
    previewName.textContent = nameInput.value || "Your Name";
});

emailInput.addEventListener("input", () => {
    previewEmail.textContent = emailInput.value || "your@email.com";
});

passwordInput.addEventListener("input", () => {
    previewPassword.textContent = passwordInput.value ? "••••••••" : "••••••••";
});


// =====================================
// Save changes (UNCHANGED)
// =====================================
saveBtn.addEventListener("click", () => {
    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const pass = passwordInput.value.trim();
    const confirm = confirmPasswordInput.value.trim();

    if (!name || !email) {
        errorMsg.textContent = "Name and email cannot be empty.";
        return;
    }

    if (!email.includes("@")) {
        errorMsg.textContent = "Enter a valid email.";
        return;
    }

    if (pass && pass !== confirm) {
        errorMsg.textContent = "Passwords do not match.";
        return;
    }

    errorMsg.style.color = "#00a651";
    errorMsg.textContent = "Profile updated!";
});
