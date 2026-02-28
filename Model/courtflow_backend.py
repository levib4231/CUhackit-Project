"""
CourtFlow Backend - Clemson Basketball Tracking System

This file handles:
1. Registering a player to a court (check-in)
2. Checking a player out
3. Getting live court occupancy
4. Updating court status automatically

Tech Stack:
- Flask (API framework)
- psycopg2 (PostgreSQL connection)

Flask → creates the web server.
request → lets you read data sent from the frontend.
jsonify → converts Python dictionaries into JSON responses.
session → stores logged-in user information securely.

Flask is a lightweight web framework. It handles HTTP requests like:
POST /checkin
GET /court/1

import psycopg2
This is the PostgreSQL driver for Python.
It allows Python to:
Connect to Postgres database
Run SQL queries
Insert, update, retrieve data
It is a bridge between Python and PostgreSQL.

Features:
- JWT authentication
- Prevent double check-in
- Prevent race conditions (transaction locking)
- Auto timeout cleanup
- Live player list
- Supabase PostgreSQL connection
"""

from multiprocessing.connection import Client

from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd
from flask_cors import CORS
from twelve_labs_client import TwelveLabsBranch


load_dotenv()

app = Flask(__name__)
CORS(app)

# =====================================================
# SUPABASE DATABASE CONNECTION (ENV VARIABLES REQUIRED)
# =====================================================

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "database": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "port": os.environ.get("DB_PORT")
}

JWT_SECRET = os.environ.get("JWT_SECRET")


def get_db_connection():
    """
    Opens new database connection for each request.
    """
    return psycopg2.connect(**DB_CONFIG)


# =====================================================
# JWT AUTHENTICATION HELPER
# =====================================================

def verify_jwt(token):
    """
    Verifies JWT and extracts user_id.
    """
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_request():
    """
    Extracts JWT from Authorization header.
    Header must be:
    Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    try:
        token = auth_header.split(" ")[1]
        return verify_jwt(token)
    except:
        return None


# =====================================================
# AUTO CLEANUP (2 HOUR TIMEOUT)
# =====================================================

def cleanup_expired_sessions(cursor):
    """
    Removes sessions older than 2 hours.
    """
    cursor.execute("""
        UPDATE "Sessions"
        SET check_out_at = NOW()
        WHERE check_out_at IS NULL
        AND check_in_at < NOW() - INTERVAL '2 hours';
    """)


# =====================================================
# CHECK-IN ENDPOINT
# =====================================================

@app.route("/checkin", methods=["POST"])
def check_in():

    user_id = get_user_from_request()

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    court_id = data.get("court_id")

    if not court_id:
        return jsonify({"error": "court_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        # Start transaction
        conn.autocommit = False

        # 1️⃣ Cleanup expired sessions first
        cleanup_expired_sessions(cursor)

        # 2️⃣ Prevent double check-in
        cursor.execute("""
            SELECT 1 FROM "Sessions"
            WHERE user_id = %s
            AND check_out_at IS NULL;
        """, (user_id,))
        if cursor.fetchone():
            return jsonify({"error": "Already checked into a court"}), 400

        # 3️⃣ Lock court row (prevents race condition)
        cursor.execute("""
            SELECT max_capacity
            FROM "Courts"
            WHERE id = %s
            FOR UPDATE;
        """, (court_id,))
        court = cursor.fetchone()

        if not court:
            return jsonify({"error": "Court not found"}), 404

        max_capacity = court["max_capacity"]

        # 4️⃣ Count active players
        cursor.execute("""
            SELECT COUNT(*) FROM "Sessions"
            WHERE court_id = %s
            AND check_out_at IS NULL;
        """, (court_id,))
        current_players = cursor.fetchone()[0]

        if current_players >= max_capacity:
            return jsonify({"error": "Court is full"}), 403

        # 5️⃣ Insert new session
        cursor.execute("""
            INSERT INTO "Sessions" (user_id, court_id)
            VALUES (%s, %s);
        """, (user_id, court_id))

        # 6️⃣ Update court status
        new_count = current_players + 1
        status = "Full" if new_count >= max_capacity else "Open"

        cursor.execute("""
            UPDATE "Courts"
            SET status = %s
            WHERE id = %s;
        """, (status, court_id))

        conn.commit()

        return jsonify({
            "message": "Checked in successfully",
            "current_players": new_count,
            "max_capacity": max_capacity,
            "status": status
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =====================================================
# CHECK-OUT ENDPOINT
# =====================================================

def _check_out_user(user_id):
    """
    Core transactional logic for checking out a user.
    Returns a tuple of (success: bool, message: str/dict, status_code: int).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False

        cursor.execute("""
            UPDATE "Sessions"
            SET check_out_at = NOW()
            WHERE user_id = %s
            AND check_out_at IS NULL
            RETURNING court_id;
        """, (user_id,))

        result = cursor.fetchone()

        if not result:
            return False, {"error": "No active session"}, 404

        court_id = result[0]

        # Update court status after checkout
        cursor.execute("""
            SELECT COUNT(*) FROM "Sessions"
            WHERE court_id = %s
            AND check_out_at IS NULL;
        """, (court_id,))
        remaining = cursor.fetchone()[0]

        cursor.execute("""
            SELECT max_capacity FROM "Courts"
            WHERE id = %s;
        """, (court_id,))
        max_capacity = cursor.fetchone()[0]

        status = "Full" if remaining >= max_capacity else "Open"

        cursor.execute("""
            UPDATE "Courts"
            SET status = %s
            WHERE id = %s;
        """, (status, court_id))

        conn.commit()
        return True, {"message": "Checked out successfully"}, 200

    except Exception as e:
        conn.rollback()
        return False, {"error": str(e)}, 500

    finally:
        cursor.close()
        conn.close()


@app.route("/checkout", methods=["POST"])
def check_out():

    user_id = get_user_from_request()

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    success, message, status_code = _check_out_user(user_id)
    
    return jsonify(message), status_code


# =====================================================
# GET COURT STATUS + PLAYER LIST
# =====================================================

@app.route("/court/<int:court_id>", methods=["GET"])
def get_court_status(court_id):

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cleanup_expired_sessions(cursor)

        cursor.execute("""
            SELECT name, max_capacity, status
            FROM "Courts"
            WHERE id = %s;
        """, (court_id,))
        court = cursor.fetchone()

        if not court:
            return jsonify({"error": "Court not found"}), 404

        cursor.execute("""
            SELECT p.fname, p.lname
            FROM "Sessions" s
            JOIN "Profiles" p ON s.user_id = p.id
            WHERE s.court_id = %s
            AND s.check_out_at IS NULL;
        """, (court_id,))
        players = cursor.fetchall()

        player_list = [
            {"fname": p["fname"], "lname": p["lname"]}
            for p in players
        ]

        return jsonify({
            "court_name": court["name"],
            "status": court["status"],
            "max_capacity": court["max_capacity"],
            "current_players": len(player_list),
            "players": player_list
        })

    finally:
        cursor.close()
        conn.close()


# =====================================================
# FUNCTIONS FROM DBCLIENT
# =====================================================

def get_active_sessions():
    """Fetch all players currently on a court (check_out_at is null)."""
    response = supabase.table("Sessions") \
        .select("id, check_in_at, Profiles(fname, lname), Courts(name)") \
        .is_("check_out_at", "null") \
        .execute()
    return response.data

def check_in_player(qr_token: str, court_id: int):
    """Business logic to check in a player via their QR code."""
    # 1. Find user by token
    user = supabase.table("Profiles").select("id").eq("qr_code_token", qr_token).single().execute()
    
    if not user.data:
        return "Error: Invalid QR Code"

    # 2. Create the session
    new_session = {
        "user_id": user.data['id'],
        "court_id": court_id
    }
    
    result = supabase.table("Sessions").insert(new_session).execute()
    return f"Success! Checked in user ID: {user.data['id']}"

def check_out_player(user_id: int):
    """
    Finds the active session for a user and sets the check_out_at timestamp to now.
    Uses the core transactional checkout logic.
    """
    success, message, status_code = _check_out_user(user_id)
    
    if success:
        print(f"User {user_id} checked out successfully.")
        return {"success": True, "data": message}
    else:
        print(f"No active session found for User {user_id}.")
        return {"success": False, "message": message.get("error", "Unknown error")}
    
def get_dashboard_stats():
    """
    Fetches high-level KPIs for the top of the dashboard.
    """
    active_count = supabase.table("Sessions").select("id", count="exact").is_("check_out_at", "null").execute()
    
    today_start = "2026-02-27T00:00:00Z" # You'd generate this dynamically
    daily_count = supabase.table("Sessions").select("id", count="exact").gte("check_in_at", today_start).execute()
    
    return {
        "live_players": active_count.count,
        "daily_total": daily_count.count
    }

def get_utilization_data():
    """
    Returns data for a Bar Chart showing court occupancy.
    """
    response = supabase.table("court_utilization").select("*").execute()
    return response.data

def get_heatmap_data():
    """
    Returns data for a Line Chart showing busiest hours.
    """
    response = supabase.table("hourly_traffic").select("*").execute()
    return response.data


def get_session_insights():
    # Fetch completed sessions
    response = supabase.table("Sessions").select("check_in_at, check_out_at").not_.is_("check_out_at", "null").execute()
    
    df = pd.DataFrame(response.data)
    
    # Calculate duration
    df['check_in_at'] = pd.to_datetime(df['check_in_at'])
    df['check_out_at'] = pd.to_datetime(df['check_out_at'])
    df['duration_minutes'] = (df['check_out_at'] - df['check_in_at']).dt.total_seconds() / 60
    
    return {
        "avg_duration": round(df['duration_minutes'].mean(), 1),
        "max_duration": round(df['duration_minutes'].max(), 1)
    }


tl_branch = TwelveLabsBranch()

def handle_checkout_and_analyze(qr_id, video_file):
    # 1. Standard Check-out
    result = check_out_player(qr_id) # Your existing int8 function
    
    if result["success"]:
        # 2. Trigger TwelveLabs Analysis
        # Note: In a real gym, 'video_file' would be pulled from the court's camera
        player_name = (supabase.table("Profiles")
                       .select("fname, lname")
                       .eq("qr_code_id", qr_id)
                       .single().execute().data)
        
        full_name = f"{player_name['fname']} {player_name['lname']}"
        
        # Find highlights for the demo
        highlights = tl_branch.find_player_highlights(full_name, "scoring a point")
        
        return {
            "status": "Checked Out",
            "highlights_found": len(highlights),
            "clips": highlights[:3] # Return top 3 clips for the UI
        }
    
def join_team(user_id: int, team_name: str):
    """Adds a user to a team by name."""
    try:
        # 1. Get the Team ID
        team = supabase.table("Teams").select("id").eq("name", team_name).single().execute()
        if not team.data:
            return {"success": False, "message": "Team not found."}
        
        # 2. Insert Membership
        response = supabase.table("Memberships").insert({
            "user_id": user_id,
            "team_id": team.data['id']
        }).execute()
        
        return {"success": True, "message": f"Joined {team_name}!"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def leave_team(user_id: int, team_id: int):
    """Removes a user from a specific team."""
    try:
        response = supabase.table("Memberships") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("team_id", team_id) \
            .execute()
        
        return {"success": True, "message": "Left the team."}
    except Exception as e:
        return {"success": False, "error": str(e)}

# =====================================================
# DASHBOARD API
# =====================================================

@app.route("/api/dashboard_stats", methods=["GET"])
def api_get_dashboard_stats():
    """
    API endpoint for the main dashboard KPIs.
    """
    stats = get_dashboard_stats()
    return jsonify(stats)

@app.route("/api/utilization_data", methods=["GET"])
def api_get_utilization_data():
    """
    API endpoint for court utilization data.
    """
    data = get_utilization_data()
    return jsonify(data)

# =====================================================
# PRODUCTION SERVER
# =====================================================

if __name__ == "__main__":
    app.run()
