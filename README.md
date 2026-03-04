# CUhackit-Project

This is a Full Stack web app made in CUHackit26 hackathon at Clemson University. The goal was to build a front‑end interface that lets users create accounts, join teams, find games, and keep track of scores and upcoming matches. It's mostly HTML/CSS/JS and Python for backend to handle authentication.

## Structure

- `CUTRACKIT/` – the client-side code. Each page has its own folder with `.html`, `.css`, and `.js` files.
- `Model/` – Python modules that implement authentication logic and communicate with the database (mostly for demo purposes).
- `View/` – the Flask app that ties the front end and back end together.
- `Client/` – some extra scripts for testing or separate components.

## Getting Started

You can preview the UI by opening `CUTRACKIT/index.html` in your browser or running a simple file server:
```
cd CUTRACKIT
python3 -m http.server
```

To run the backend, install the requirements and start the Flask app:
```
cd Model
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ../View/app.py
```
2026 CUhackit Hackathon
