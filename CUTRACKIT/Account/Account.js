console.log("Account JS running");
const BACKEND_URL = "http://127.0.0.1:5000"; // change when deployed

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

    const token = localStorage.getItem("cutrackit_jwt");

    if (!token) {
        console.log("User not logged in.");
        return;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/profile`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error);
        }

        const fullName = `${data.fname || ""} ${data.lname || ""}`.trim();

        // Fill form inputs
        nameInput.value = fullName;
        emailInput.value = data.email;

        // Update preview
        previewName.textContent = fullName || "Your Name";
        previewEmail.textContent = data.email || "your@email.com";

    } catch (error) {
        console.error("Profile fetch failed:", error.message);
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
