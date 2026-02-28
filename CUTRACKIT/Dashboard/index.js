// 1. Initialize Supabase Client at the very top
const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

// 2. Function to populate the dropdown
async function populateGymDropdown() {
    try {
        console.log("Attempting to fetch data from 'Courts' table...");
        
        const { data, error } = await supabaseClient
            .from('Courts') 
            .select('name')
            .order('name', { ascending: true });

        if (error) {
            console.error("Supabase Error:", error.message);
            return;
        }

        console.log("Data received from Supabase:", data);

        const gymSelect = document.getElementById('gymSelect');
        if (!gymSelect) {
            console.error("Could not find HTML element with ID 'gymSelect'");
            return;
        }

        if (data && data.length > 0) {
            // Keep the placeholder, clear others
            gymSelect.innerHTML = '<option value="">Select Court</option>';
            
            data.forEach(gym => {
                const option = document.createElement('option');
                option.value = gym.name;
                option.textContent = gym.name;
                gymSelect.appendChild(option);
            });
            console.log("Dropdown successfully populated!");
        } else {
            console.warn("No data found in the 'Courts' table.");
        }
    } catch (err) {
        console.error("Unexpected Script Error:", err.message);
    }
}

// 3. Carousel and Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Run the dropdown fetch immediately on load
    populateGymDropdown();

    // Carousel Logic
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