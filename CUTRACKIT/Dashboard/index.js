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

// Fetch live player count
async function fetchPlayerCount() {
    try {
        const response = await fetch('/api/dashboard_stats');
        if (response.ok) {
            const data = await response.json();
            const countElement = document.querySelector('.player-count');
            if (countElement && data.live_players !== undefined) {
                countElement.textContent = data.live_players;
            }
        } else {
            console.error('Failed to fetch player count:', response.statusText);
        }
    } catch (error) {
        console.error('Error fetching player count:', error);
    }
}

// Call on load
document.addEventListener('DOMContentLoaded', fetchPlayerCount);

