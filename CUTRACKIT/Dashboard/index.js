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
        option.value = court.id; 
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

async function updatePlayerCountUI() {
    // Count sessions where check_out_at IS NULL
    const { count, error } = await supabaseClient
        .from('Sessions')
        .select('*', { count: 'exact', head: true })
        .is('check_out_at', null);

    if (error) {
        console.error("Error fetching player count:", error.message);
        return;
    }

    const countDisplay = document.querySelector('.player-count');
    if (countDisplay) {
        countDisplay.textContent = count || 0;
    }
}

// ============================
// Toggle Check-In/Out Logic
// ============================
async function handleToggleCheckIn() {
    const gymSelect = document.getElementById('gymSelect');
    const courtId = gymSelect.value;
    const statusText = document.getElementById("statusText");
    const checkInBtn = document.getElementById("checkInBtn");

    if (!courtId) {
        alert("Please select a court first.");
        return;
    }

    // A. Get the authenticated user (UUID)
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
    if (authError || !user) {
        alert("You must be logged in.");
        return;
    }

    // B. Find the numeric Profile ID using the auth_id
    const { data: profile, error: profileError } = await supabaseClient
        .from('Profiles')
        .select('id')
        .eq('id', user.id) // Corrected: searching by auth_id column
        .maybeSingle();

    if (profileError || !profile) {
        console.error("Profile not found:", profileError);
        alert("Error: Profile record not found in database.");
        return;
    }

    // C. Check for an active session (where check_out_at is null)
    const { data: activeSession, error: sessionError } = await supabaseClient
        .from('Sessions')
        .select('id')
        .eq('user_id', profile.id)
        .is('check_out_at', null)
        .maybeSingle();

    if (sessionError) {
        console.error("Session lookup error:", sessionError);
        return;
    }

    if (activeSession) {
        // --- ACTION: CHECK OUT ---
        const { error: updateError } = await supabaseClient
            .from('Sessions')
            .update({ check_out_at: new Date().toISOString() })
            .eq('id', activeSession.id);

        if (!updateError) {
            // UI Update: Switch back to Check In
            statusText.textContent = "Status: Inactive";
            checkInBtn.textContent = "Check In";
            
            await updatePlayerCountUI();
            alert("Checked out successfully!");
        } else {
            console.error("Update error:", updateError.message);
        }
    } else {
        // --- ACTION: CHECK IN ---
        const { error: insertError } = await supabaseClient
            .from('Sessions')
            .insert([{ 
                user_id: profile.id, 
                court_id: courtId, 
                check_in_at: new Date().toISOString() 
            }]);

        if (!insertError) {
            // UI Update: Switch to Check Out
            statusText.textContent = "Status: Checked In";
            checkInBtn.textContent = "Check Out";
            
            await updatePlayerCountUI();
            alert("Checked in successfully!");
        } else {
            console.error("Insert error:", insertError.message);
        }
    }
}
// ============================
// Initialization
// ============================
document.addEventListener('DOMContentLoaded', () => {
    populateGymDropdown();
    updatePlayerCountUI();

    // Attach the toggle logic to the button in your HTML
    const checkInBtn = document.getElementById("checkInBtn");
    if (checkInBtn) {
        checkInBtn.addEventListener("click", handleToggleCheckIn);
    }
});