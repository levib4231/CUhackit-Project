// 1. Setup Supabase first so it's ready for functions to use
const supabaseUrl = 'https://cixuwmqjrcubiwhgnvlf.supabase.co';
const supabaseKey = 'sb_publishable_Miz7VAu62K_pZsVZHnGHWQ_7BUVDWmx';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

// 2. Define the Dropdown Function
async function populateGymDropdown() {
    try {
        const { data, error } = await supabaseClient
            .from('Courts') 
            .select('name')
            .order('name', { ascending: true });

        if (error) throw error;

        const gymSelect = document.getElementById('gymSelect');
        if (gymSelect && data) {
            // Keep "Select Gym" placeholder, clear hardcoded Fike/Underground
            gymSelect.innerHTML = '<option value="">Select Gym</option>';
            data.forEach(gym => {
                const option = document.createElement('option');
                option.value = gym.name;
                option.textContent = gym.name;
                gymSelect.appendChild(option);
            });
        }
    } catch (err) {
        console.error('Dropdown Error:', err.message);
    }
}

// 3. Define Player Count Function
async function fetchPlayerCount() {
    try {
        const { count, error } = await supabaseClient
            .from('Sessions') 
            .select('*', { count: 'exact', head: true })
            .is('check_out_at', null);

        if (error) throw error;
        const countElement = document.querySelector('.player-count');
        if (countElement) countElement.textContent = count ?? 0;
    } catch (err) {
        console.error('Counter Error:', err.message);
    }
}

// 4. Initialize everything once the HTML is loaded
document.addEventListener('DOMContentLoaded', () => {
    fetchPlayerCount();
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