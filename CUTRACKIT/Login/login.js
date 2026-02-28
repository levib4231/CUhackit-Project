// Clear any old custom tokens
window.addEventListener('DOMContentLoaded', () => {
    localStorage.removeItem('cutrackit_jwt');
    localStorage.removeItem('cutrackit_user_id');
    localStorage.removeItem('cutrackit_profile');
});

const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);


const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");
const loginBtn = document.getElementById("loginBtn");
const errorMsg = document.getElementById("errorMsg");
const togglePassword = document.getElementById("togglePassword");

// Show/Hide Password
togglePassword.addEventListener("click", () => {
    const type = passwordInput.type === "password" ? "text" : "password";
    passwordInput.type = type;
});

// Login using Supabase Auth
loginBtn.addEventListener("click", async () => {

    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    if (!email || !password) {
        errorMsg.style.color = "#ff4d4d";
        errorMsg.textContent = "Please fill out all fields.";
        return;
    }

    errorMsg.style.color = "white";
    errorMsg.textContent = "Logging in...";

    const { data, error } = await supabaseClient.auth.signInWithPassword({
        email,
        password
    });

    if (error) {
        errorMsg.style.color = "#ff4d4d";
        errorMsg.textContent = error.message;
        return;
    }

    // Store access token for backend usage
    localStorage.setItem("cutrackit_jwt", data.session.access_token);

    errorMsg.style.color = "#00ff99";
    errorMsg.textContent = "Login successful! Redirecting...";

    setTimeout(() => {
        window.location.href = "../Dashboard/index.html";
    }, 500);
});
