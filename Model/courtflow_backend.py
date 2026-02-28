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
import jwt

# =====================================================
# LOAD ENV VARIABLES
# =====================================================
load_dotenv()
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")


app = Flask(__name__)
CORS(app)

# Health check route
@app.route("/")
def health():
    return jsonify({"status": "CourtFlow backend running"})

# this route is a protected endpoint that retrieves the user's profile information. It first extracts the user ID from the Supabase JWT token, then queries the PostgreSQL database for the user's profile details (first name, last name, and email) and returns them as a JSON response. If the user is not authenticated or if the profile is not found, it returns appropriate error messages.
@app.route("/profile", methods=["GET"])
def get_profile():

    user_id = get_profile_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cursor.execute("""
            SELECT fname, lname, email
            FROM "Profiles"
            WHERE id = %s;
        """, (user_id,))

        profile = cursor.fetchone()

        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        return jsonify({
            "fname": profile["fname"],
            "lname": profile["lname"],
            "email": profile["email"]
        })

    finally:
        cursor.close()
        conn.close()
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

# get_db_connection() is a helper function to connect to the PostgreSQL database using psycopg2. It uses the DB_CONFIG dictionary for connection parameters and includes error handling to print any connection errors that occur.
def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        raise


# =====================================================
# HELPER: GET PROFILE ID FROM SUPABASE TOKEN
# =====================================================
def get_profile_id_from_token():

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        token = auth_header.split(" ")[1]

        # Decode + verify token manually
        decoded = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        auth_uuid = decoded.get("sub")

        if not auth_uuid:
            return None

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

    except Exception as e:
        print(f"JWT decoding error: {e}")
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
        conn.commit()

        # Prevent double check-in
        cursor.execute("""
            SELECT 1 FROM "Sessions"
            WHERE user_id = %s
            AND check_out_at IS NULL;
        """, (user_id,))
        if cursor.fetchone():
            conn.rollback()
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
    app.run(host="0.0.0.0", port=5500)