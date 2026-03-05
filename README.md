# CUTRACKIT

CUTRACKIT is a web application built during CUhackit 2026 to help organize recreational games and track player participation. The platform allows users to create accounts, join teams, select courts, and check in or check out of games while tracking how many players are currently active.

🚀 Live Demo  
https://cuhackit-project.vercel.app/

💻 GitHub Repository  
https://github.com/levib4231/CUhackit-Project

---

## Features

- User account creation and authentication
- QR code access to quickly open the platform
- Court selection before participating in games
- Check-in and check-out system for tracking active players
- Real-time player status retrieved from the database
- Account page displaying player information and participation data
- Team and game tracking functionality

---

## How It Works

Players can scan a QR code that directs them to the web application. If they do not have an account, they must first create one and then sign in.

After logging in, users can select the court where they are playing and perform check-in or check-out actions. The system stores this information in the database and retrieves data dynamically to display which players are currently checked in or checked out.

Each user also has an account page where their details and activity are displayed.

---

## Tech Stack

Frontend
- HTML
- CSS
- JavaScript

Backend
- Python
- Flask

Database
- Supabase

Deployment
- Vercel

---

## Project Structure

CUTRACKIT/ – Frontend interface (HTML, CSS, JS)

Model/ – Backend modules and authentication logic

View/ – Flask application connecting frontend and backend

Client/ – Additional scripts and components

---

## Running the Project Locally

Clone the repository

```bash
git clone https://github.com/levib4231/CUhackit-Project
cd CUhackit-Project

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
