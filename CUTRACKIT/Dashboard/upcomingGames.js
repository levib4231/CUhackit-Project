let upcomingGames = [
    {
        opponent: "Upstate Warriors",
        type: "3v3",
        date: "March 2, 2026",
        time: "4:00 PM"
    },
    {
        opponent: "Clemson Elite",
        type: "5v5",
        date: "March 5, 2026",
        time: "6:30 PM"
    },
    {
        opponent: "Solo Kings",
        type: "1v1",
        date: "March 7, 2026",
        time: "2:00 PM"
    }
];

const gamesList = document.getElementById("gamesList");

function renderGames() {
    gamesList.innerHTML = "";
    upcomingGames.forEach(game => {
        const div = document.createElement("div");
        div.classList.add("game-item");
        div.innerHTML = `
            <h3>vs ${game.opponent}</h3>
            <p>Match Type: ${game.type}</p>
            <p>Date: ${game.date}</p>
            <p>Time: ${game.time}</p>
        `;
        gamesList.appendChild(div);
    });
}

renderGames();
