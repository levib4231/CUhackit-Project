const nameInput = document.getElementById("nameInput");
const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");
const confirmPasswordInput = document.getElementById("confirmPasswordInput");
const saveBtn = document.getElementById("saveBtn");
const errorMsg = document.getElementById("errorMsg");

const previewName = document.getElementById("previewName");
const previewEmail = document.getElementById("previewEmail");
const previewPassword = document.getElementById("previewPassword");

// Live preview updates
nameInput.addEventListener("input", () => {
    previewName.textContent = nameInput.value || "Your Name";
});

emailInput.addEventListener("input", () => {
    previewEmail.textContent = emailInput.value || "your@email.com";
});

passwordInput.addEventListener("input", () => {
    previewPassword.textContent = passwordInput.value ? "••••••••" : "••••••••";
});

// Save changes
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
