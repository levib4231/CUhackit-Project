
// Auth0 Configuration
const auth0Domain = "dev-scz0be2kycl7oqlb.us.auth0.com";
const auth0ClientId = "vK85nT8Su7VG1C9DrSDiGvgqkGpNzVfd";
const auth0Audience = "https://dev-scz0be2kycl7oqlb.us.auth0.com/api/v2/";

let auth0Client = null;
let accessToken = null;

async function initAuth() {
    auth0Client = await createAuth0Client({
        domain: auth0Domain,
        client_id: auth0ClientId,
        audience: auth0Audience,
        redirect_uri: window.location.origin + "../Dashboard/index.html"
    });

    // Check if handling a callback from Auth0
    if (window.location.search.includes("code=") && window.location.search.includes("state=")) {
        await auth0Client.handleRedirectCallback();
        window.history.replaceState({}, document.title, "../Dashboard/index.html");
    }

    // Check if user is authenticated
    const isAuthenticated = await auth0Client.isAuthenticated();
    
    if (!isAuthenticated) {
        // Redirect to login if not authenticated
        window.location.replace("../Login/login.html");
        return;
    }

    // Get the access token for API calls
    accessToken = await auth0Client.getTokenSilently();
    localStorage.setItem("access_token", accessToken);

    // Get user info and sync with backend
    const user = await auth0Client.getUser();
    await syncProfile(user);
}

async function syncProfile(user) {
    try {
        const response = await fetch(`${BACKEND_URL}/sync_profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({
                email: user.email,
                fname: user.given_name || "",
                lname: user.family_name || ""
            })
        });
        const data = await response.json();
        console.log("Profile Sync:", data);
    } catch (error) {
        console.error("Error syncing profile:", error);
    }
}

// Intercept fetch requests to add Authorization header
const originalFetch = window.fetch;
window.fetch = async function() {
    let [resource, config] = arguments;
    
    if (typeof resource === 'string' && resource.includes(BACKEND_URL) && accessToken) {
        config = config || {};
        config.headers = config.headers || {};
        config.headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    return originalFetch(resource, config);
};

// Start Auth Process when DOM is ready
window.addEventListener('DOMContentLoaded', initAuth);

// Supabase client
const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

// Change this when deployed
const BACKEND_URL = "http://localhost:5000";


// ============================
// Populate Court Dropdown
// ============================
async function populateGymDropdown() {

    const { data, error } = await supabaseClient
        .from('Courts')
        .select('id, name')
        .order('name', { ascending: true });

    if (error) {
        console.error(error.message);
        return;
    }

    const gymSelect = document.getElementById('gymSelect');

    gymSelect.innerHTML = '<option value="">Select Court</option>';

    data.forEach(court => {
        const option = document.createElement('option');
        option.value = court.id; // IMPORTANT: use ID now
        option.textContent = court.name;
        gymSelect.appendChild(option);
    });
}


// ============================
// CHECK IN
// ============================
async function checkIn() {

    const select = document.getElementById("gymSelect");
    const courtId = select.value;

    if (!courtId) {
        alert("Select a court first.");
        return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
        alert("You must login first.");
        return;
    }

    const response = await fetch(`${BACKEND_URL}/checkin`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            court_id: courtId
        })
    });

    const result = await response.json();

    if (response.ok) {
        alert("Checked in successfully!");
    } else {
        alert(result.error);
    }
}


// ============================
// CHECK OUT
// ============================
async function checkOut() {

    const token = localStorage.getItem("access_token");

    if (!token) {
        alert("You must login first.");
        return;
    }

    const response = await fetch(`${BACKEND_URL}/checkout`, {
        method: "POST",
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    const result = await response.json();

    if (response.ok) {
        alert("Checked out successfully!");
    } else {
        alert(result.error);
    }
}


// ============================
// Load page
// ============================
document.addEventListener('DOMContentLoaded', () => {

    populateGymDropdown();

    // Carousel logic (unchanged)
    const track = document.getElementById("carouselTrack");
    const nextBtn = document.getElementById("nextBtn");
    const prevBtn = document.getElementById("prevBtn");
    let position = 0;
    const cardWidth = 320;

    if (track && nextBtn && prevBtn) {
        const totalCards = track.children.length;
        const maxPosition = -(cardWidth * (totalCards - 3));

        nextBtn.addEventListener("click", () => {
            if (position > maxPosition) {
                position -= cardWidth;
                track.style.transform = `translateX(${position}px)`;
            }
        });

        prevBtn.addEventListener("click", () => {
            if (position < 0) {
                position += cardWidth;
                track.style.transform = `translateX(${position}px)`;
            }
        });
    }
});

// ... existing initialization ...

async function handleToggleCheckIn() {
    const gymSelect = document.getElementById('gymSelect');
    const selectedCourt = gymSelect.value;

    if (!selectedCourt) {
        alert("Please select a court first.");
        return;
    }

    // A. Get the logged-in user
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
    
    if (authError || !user) {
        alert("You must be logged in to check in.");
        return;
    }

    // B. Check if user is ALREADY checked into THIS court
    const { data: existingCheckIn, error: fetchError } = await supabaseClient
        .from('CheckIns')
        .select('*')
        .eq('user_id', user.id)
        .eq('court_name', selectedCourt)
        .single();

    if (existingCheckIn) {
        // --- LOGIC: CHECK OUT ---
        // 1. Remove the check-in record
        const { error: deleteError } = await supabaseClient
            .from('CheckIns')
            .delete()
            .eq('user_id', user.id)
            .eq('court_name', selectedCourt);

        if (!deleteError) {
            // 2. Decrement the count in the Courts table
            await supabaseClient.rpc('decrement_court_count', { court_row_name: selectedCourt });
            alert("Checked out successfully!");
        }
    } else {
        // --- LOGIC: CHECK IN ---
        // 1. Create the check-in record
        const { error: insertError } = await supabaseClient
            .from('CheckIns')
            .insert([{ user_id: user.id, court_name: selectedCourt }]);

        if (!insertError) {
            // 2. Increment the count in the Courts table
            await supabaseClient.rpc('increment_court_count', { court_row_name: selectedCourt });
            alert("Checked in successfully!");
        }
    }
}