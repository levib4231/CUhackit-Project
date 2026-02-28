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
loginBtn.addEventListener("click", () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    if (!email || !password) {
        errorMsg.textContent = "Please fill out all fields.";
        return;
    }

    if (!email.includes("@")) {
        errorMsg.textContent = "Enter a valid email.";
        return;
    }

    errorMsg.style.color = "#00ff99";
    errorMsg.textContent = "Login successful!";
});
