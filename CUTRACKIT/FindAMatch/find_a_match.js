let matches = [
    {
        team: "Upstate Warriors",
        type: "3v3",
        date: "2026-03-02",
        time: "16:00",
        notes: "Court 2 available"
    },
    {
        team: "Clemson Elite",
        type: "5v5",
        date: "2026-03-05",
        time: "18:30",
        notes: "Full court requested"
    },
    {
        team: "Solo Kings",
        type: "1v1",
        date: "2026-03-07",
        time: "14:00",
        notes: "Bring your own ball"
    }
];

const matchList = document.getElementById("matchList");
const matchType = document.getElementById("matchType");
const matchDate = document.getElementById("matchDate");
const matchTime = document.getElementById("matchTime");
const matchNotes = document.getElementById("matchNotes");
const publishMatchBtn = document.getElementById("publishMatchBtn");
const createMsg = document.getElementById("createMsg");

function renderMatches() {
    matchList.innerHTML = "";

    matches.forEach(match => {
        const div = document.createElement("div");
        div.classList.add("match-item");

        div.innerHTML = `
            <h3>${match.team}</h3>
            <p>Match Type: ${match.type}</p>
            <p>Date: ${match.date}</p>
            <p>Time: ${match.time}</p>
            <p>${match.notes}</p>
            <button class="join-btn">Join Match</button>
        `;

        matchList.appendChild(div);
    });
}

publishMatchBtn.addEventListener("click", () => {
    const newMatch = {
        team: "Your Team",
        type: matchType.value,
        date: matchDate.value,
        time: matchTime.value,
        notes: matchNotes.value
    };

    matches.push(newMatch);
    renderMatches();

    createMsg.textContent = "Match published!";
    setTimeout(() => createMsg.textContent = "", 2000);
});

renderMatches();
