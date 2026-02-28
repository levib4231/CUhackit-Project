// Auth0 Login Handle
const auth0Domain = "dev-scz0be2kycl7oqlb.us.auth0.com";
const auth0ClientId = "vK85nT8Su7VG1C9DrSDiGvgqkGpNzVfd";
const auth0Audience = "https://dev-scz0be2kycl7oqlb.us.auth0.com/api/v2/";

let auth0Client = null;

window.addEventListener('DOMContentLoaded', async () => {
    // Clear old tokens for Supabase just in case
    localStorage.removeItem('access_token');
    
    // Initialize Auth0
    auth0Client = await createAuth0Client({
        domain: auth0Domain,
        client_id: auth0ClientId,
        audience: auth0Audience,
        redirect_uri: window.location.origin + "/CUTRACKIT/Dashboard/index.html"
    });

    const loginBtn = document.getElementById("loginBtn");
    
    // Redirect to Auth0 Universal Login
    loginBtn.addEventListener("click", async () => {
        const errorMsg = document.getElementById("errorMsg");
        errorMsg.style.color = "white";
        errorMsg.textContent = "Redirecting to login...";
        
        await auth0Client.loginWithRedirect({
            redirect_uri: window.location.origin + "/CUTRACKIT/Dashboard/index.html"
        });
    });
});
