// Global Logout Logic: If user lands on login page, clear any existing session
window.addEventListener('DOMContentLoaded', () => {
    localStorage.removeItem('cutrackit_jwt');
    localStorage.removeItem('cutrackit_user_id');
    localStorage.removeItem('cutrackit_profile');
});

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

// Login Validation
loginBtn.addEventListener("click", async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    if (!email || !password) {
        errorMsg.style.color = "#ff4d4d";
        errorMsg.textContent = "Please fill out all fields.";
        return;
    }

    if (!email.includes("@")) {
        errorMsg.style.color = "#ff4d4d";
        errorMsg.textContent = "Enter a valid email.";
        return;
    }

    errorMsg.style.color = "white";
    errorMsg.textContent = "Logging in...";

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            errorMsg.style.color = "#00ff99";
            errorMsg.textContent = "Login successful! Redirecting...";

            // Save state to localStorage
            localStorage.setItem('cutrackit_jwt', data.jwt);
            localStorage.setItem('cutrackit_user_id', data.user_id);
            localStorage.setItem('cutrackit_profile', JSON.stringify(data.profile));

            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 500);
        } else {
            errorMsg.style.color = "#ff4d4d";
            errorMsg.textContent = data.error || "Invalid login credentials.";
        }
    } catch (error) {
        console.error("Login failed:", error);
        errorMsg.style.color = "#ff4d4d";
        errorMsg.textContent = "An error occurred during login. Please try again.";
    }
});
