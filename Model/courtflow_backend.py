"""
CourtFlow Backend
Using Supabase Auth + PostgreSQL

Features:
- Supabase JWT validation (official way)
- Prevent double check-in
- Prevent race conditions
- Auto timeout cleanup
- Live player list
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client
import psycopg2
import psycopg2.extras
import os

# =====================================================
# LOAD ENV VARIABLES
# =====================================================
load_dotenv()

app = Flask(__name__)
CORS(app)

# =====================================================
# SUPABASE CLIENT SETUP
# =====================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =====================================================
# DATABASE CONNECTION (DIRECT POSTGRES)
# =====================================================
DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "database": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "port": os.environ.get("DB_PORT")
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# =====================================================
# HELPER: GET PROFILE ID FROM SUPABASE TOKEN
# =====================================================
def get_profile_id_from_token():
    """
    1. Extract Bearer token
    2. Validate with Supabase
    3. Get user UUID
    4. Map to Profiles.id
    """

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        token = auth_header.split(" ")[1]

        # Validate token with Supabase
        user = supabase.auth.get_user(token)

        if not user:
            return None

        auth_uuid = user.user.id

        # Map UUID to Profiles.id
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM public."Profiles"
            WHERE auth_id = %s;
        """, (auth_uuid,))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if not result:
            return None

        return result[0]

    except Exception:
        return None

# =====================================================
# AUTO CLEANUP (2 HOUR TIMEOUT)
# =====================================================
def cleanup_expired_sessions(cursor):
    cursor.execute("""
        UPDATE "Sessions"
        SET check_out_at = NOW()
        WHERE check_out_at IS NULL
        AND check_in_at < NOW() - INTERVAL '2 hours';
    """)

# =====================================================
# CHECK-IN
# =====================================================
@app.route("/checkin", methods=["POST"])
def check_in():

    user_id = get_profile_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    court_id = data.get("court_id")

    if not court_id:
        return jsonify({"error": "court_id required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        conn.autocommit = False

        # Cleanup old sessions
        cleanup_expired_sessions(cursor)

        # Prevent double check-in
        cursor.execute("""
            SELECT 1 FROM "Sessions"
            WHERE user_id = %s
            AND check_out_at IS NULL;
        """, (user_id,))
        if cursor.fetchone():
            return jsonify({"error": "Already checked in"}), 400

        # Lock court row
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

        # Count active players
        cursor.execute("""
            SELECT COUNT(*) FROM "Sessions"
            WHERE court_id = %s
            AND check_out_at IS NULL;
        """, (court_id,))
        current_players = cursor.fetchone()[0]

        if current_players >= max_capacity:
            return jsonify({"error": "Court is full"}), 403

        # Insert session
        cursor.execute("""
            INSERT INTO "Sessions" (user_id, court_id)
            VALUES (%s, %s);
        """, (user_id, court_id))

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
# CHECK-OUT
# =====================================================
@app.route("/checkout", methods=["POST"])
def check_out():

    user_id = get_profile_id_from_token()
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

        # Update court status
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
# GET COURT STATUS
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

        return jsonify({
            "court_name": court["name"],
            "status": court["status"],
            "max_capacity": court["max_capacity"],
            "current_players": len(players),
            "players": [
                {"fname": p["fname"], "lname": p["lname"]}
                for p in players
            ]
        })

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run()