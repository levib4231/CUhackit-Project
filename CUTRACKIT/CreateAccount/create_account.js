// Auth0 Registration Handle
const auth0Domain = "dev-scz0be2kycl7oqlb.us.auth0.com";
const auth0ClientId = "vK85nT8Su7VG1C9DrSDiGvgqkGpNzVfd";
const auth0Audience = "https://dev-scz0be2kycl7oqlb.us.auth0.com/api/v2/";

let auth0Client = null;

window.addEventListener('DOMContentLoaded', async () => {
    // Initialize Auth0
    auth0Client = await createAuth0Client({
        domain: auth0Domain,
        client_id: auth0ClientId,
        audience: auth0Audience,
        redirect_uri: window.location.origin + "/CUTRACKIT/Dashboard/index.html"
    });

    const createBtn = document.getElementById("createBtn");
    
    // Redirect to Auth0 Universal Login (signup tab)
    createBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        const errorMsg = document.getElementById("errorMsg");
        errorMsg.style.color = "white";
        errorMsg.textContent = "Redirecting to account creation...";
        
        await auth0Client.loginWithRedirect({
            redirect_uri: window.location.origin + "/CUTRACKIT/Dashboard/index.html",
            authorizationParams: {
                screen_hint: 'signup'
            }
        });
    });
});
