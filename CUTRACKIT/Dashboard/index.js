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
    const select = document.getElementById("gymSelect");
    const courtId = select.value;

    if (!courtId) {
        alert("Please select a court first.");
        return;
    }

    // Get current user session
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
    
    if (authError || !user) {
        alert("You must be logged in to check in.");
        return;
    }

    // 1. Check for existing check-in
    const { data: existing, error: fetchError } = await supabaseClient
        .from('CheckIns')
        .select('id, court_id')
        .eq('user_id', user.id)
        .maybeSingle(); // Returns null instead of error if not found

    if (fetchError) {
        console.error("Fetch Error:", fetchError.message);
        return;
    }

    if (existing) {
        // --- LOGIC: CHECK OUT ---
        const { error: deleteError } = await supabaseClient
            .from('CheckIns')
            .delete()
            .eq('user_id', user.id);

        if (!deleteError) {
            // Update the count on the court the user was actually checked into
            await supabaseClient.rpc('decrement_court_count', { court_id_param: existing.court_id });
            alert("Checked out successfully!");
        } else {
            console.error("Delete Error:", deleteError.message);
        }

    } else {
        // --- LOGIC: CHECK IN ---
        const { error: insertError } = await supabaseClient
            .from('CheckIns')
            .insert([{ user_id: user.id, court_id: courtId }]);

        if (!insertError) {
            await supabaseClient.rpc('increment_court_count', { court_id_param: courtId });
            alert("Checked in successfully!");
        } else {
            // If the user is already checked in elsewhere, the UNIQUE constraint will trigger this
            alert("Error: " + insertError.message);
            console.error(insertError);
        }
    }
}