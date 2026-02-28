const nameInput = document.getElementById("nameInput");
const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");
const confirmPasswordInput = document.getElementById("confirmPasswordInput");
const createBtn = document.getElementById("createBtn");
const errorMsg = document.getElementById("errorMsg");

const togglePassword = document.getElementById("togglePassword");
const toggleConfirm = document.getElementById("toggleConfirm");

// Toggle password visibility
togglePassword.addEventListener("click", () => {
    passwordInput.type = passwordInput.type === "password" ? "text" : "password";
});

toggleConfirm.addEventListener("click", () => {
    confirmPasswordInput.type = confirmPasswordInput.type === "password" ? "text" : "password";
});

// Create account validation
createBtn.addEventListener("click", () => {
    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const pass = passwordInput.value.trim();
    const confirm = confirmPasswordInput.value.trim();

    if (!name || !email || !pass || !confirm) {
        errorMsg.textContent = "Please fill out all fields.";
        return;
    }

    if (!email.includes("@")) {
        errorMsg.textContent = "Enter a valid email.";
        return;
    }

    if (pass.length < 6) {
        errorMsg.textContent = "Password must be at least 6 characters.";
        return;
    }

    if (pass !== confirm) {
        errorMsg.textContent = "Passwords do not match.";
        return;
    }

    errorMsg.style.color = "#00ff99";
    errorMsg.textContent = "Account created successfully!";
});
