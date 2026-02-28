const track = document.getElementById("carouselTrack");
const nextBtn = document.getElementById("nextBtn");
const prevBtn = document.getElementById("prevBtn");

let position = 0;
const cardWidth = 320; // 300px + 20px gap
const visibleCards = 3;
const totalCards = track.children.length;
const maxPosition = -(cardWidth * (totalCards - visibleCards));

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

async function populateGymDropdown() {
    try {
        // 1. Fetch gym names from your 'Courts' table
        const { data, error } = await supabaseClient
            .from('Courts') 
            .select('name')
            .order('name', { ascending: true });

        if (error) throw error;

        const gymSelect = document.getElementById('gymSelect');
        
        if (gymSelect && data) {
            // 2. Clear existing hardcoded options except the first "Select Court"
            gymSelect.innerHTML = '<option value="">Select Court</option>';

            // 3. Loop through data and create new options
            data.forEach(gym => {
                const option = document.createElement('option');
                option.value = gym.name;
                option.textContent = gym.name;
                gymSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading gyms:', error.message);
    }
}

// Update your DOMContentLoaded listener to include this new function
document.addEventListener('DOMContentLoaded', () => {
    fetchPlayerCount();
    populateGymDropdown();
});

// Fetch live player count
// Initialize Supabase client
// You get these from your Supabase Project Settings > API
const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co'
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx'
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);
async function fetchPlayerCount() {
    try {
        // Query the 'sessions' table (or whatever your session table is named)
        const { count, error } = await supabaseClient
            .from('Sessions') 
            .select('*', { count: 'exact', head: true }) // head: true means "just get the count, not the data"
            .is('check_out_at', null); // Filter for Null values

        if (error) throw error;

        const countElement = document.querySelector('.player-count');
        if (countElement) {
            // 'count' will be an integer representing the rows found
            countElement.textContent = count ?? 0;
        }

    } catch (error) {
        console.error('Error fetching count from Supabase:', error.message);
    }
}document.addEventListener('DOMContentLoaded', fetchPlayerCount);
// Call on load
document.addEventListener('DOMContentLoaded', fetchPlayerCount);

