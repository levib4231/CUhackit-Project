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

load_dotenv()

app = Flask(__name__)

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

@app.route("/checkout", methods=["POST"])
def check_out():

    user_id = get_user_from_request()

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

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
            return jsonify({"error": "No active session"}), 404

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

        return jsonify({"message": "Checked out successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


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
# PRODUCTION SERVER
# =====================================================

if __name__ == "__main__":
    app.run()