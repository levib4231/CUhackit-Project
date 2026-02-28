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

    // Create account validation// Ensure your supabaseClient is initialized at the top or imported
    const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
    const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx'; // Use your real anon key here
    const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

    createBtn.addEventListener("click", async (event) => { // Add 'event' here
        event.preventDefault(); // This stops the page from refreshing
        console.log("Button clicked!"); 

        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        const pass = passwordInput.value.trim();

        try {
            const { data, error } = await supabaseClient.auth.signUp({
                email: email,
                password: pass,
                options: { data: { full_name: name } }
            });

            console.log("Supabase Data:", data);   // Debug 2
            console.log("Supabase Error:", error); // Debug 3

            if (error) throw error;

            if (data.user && data.user.identities && data.user.identities.length === 0) {
                throw new Error("This email is already registered.");
            }

            errorMsg.style.color = "#00ff99";
            errorMsg.textContent = "Check your email or dashboard!";

        } catch (error) {
            console.error("Signup failed:", error.message);
            errorMsg.style.color = "#ff4d4d";
            errorMsg.textContent = error.message;
        }
    });


    function showError(text) {
        errorMsg.style.color = "#ff4d4d";
        errorMsg.textContent = text;
    }
