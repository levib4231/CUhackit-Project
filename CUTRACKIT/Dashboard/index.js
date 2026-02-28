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
