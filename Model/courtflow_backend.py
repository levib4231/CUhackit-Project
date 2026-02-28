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


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# =====================================================
# HELPER: GET PROFILE ID FROM AUTH0 TOKEN
# =====================================================
from auth0_verify import verify_jwt, get_token_auth_header, AuthError

def get_profile_id_from_token():
    """
    1. Extract Bearer token
    2. Validate with Auth0
    3. Get user user_id (sub)
    4. Map to Profiles.auth_id
    """
    try:
        token = get_token_auth_header(request)
        payload = verify_jwt(token)
        
        # Auth0 user ID is in the 'sub' claim
        auth_uuid = payload.get("sub")
        if not auth_uuid:
            return None

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

    except AuthError:
        return None
    except Exception as e:
        print(f"Error getting profile ID: {e}")
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


# =====================================================
# SYNC PROFILE AFTER AUTH0 LOGIN
# =====================================================
@app.route("/sync_profile", methods=["POST"])
def sync_profile():
    """
    Called by the frontend after a successful Auth0 login.
    Creates a row in the Profiles table if one doesn't exist for this Auth0 user.
    """
    try:
        # Require a valid Auth0 token
        token = get_token_auth_header(request)
        payload = verify_jwt(token)
        
        auth_uuid = payload.get("sub")
        if not auth_uuid:
            return jsonify({"error": "Invalid token payload, missing sub"}), 400
            
    except AuthError as e:
        return jsonify(e.error), e.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 401

    data = request.get_json() or {}
    email = data.get("email", "")
    fname = data.get("fname", "")
    lname = data.get("lname", "")

    # Fallback to defaults if missing parts
    if not fname and not lname and email:
        parts = email.split("@")[0].split(".")
        fname = parts[0].capitalize() if parts else "User"
        lname = parts[1].capitalize() if len(parts) > 1 else ""
    elif not fname:
        fname = "User"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        # Check if profile already exists
        cursor.execute("""
            SELECT id FROM public."Profiles"
            WHERE auth_id = %s;
        """, (auth_uuid,))

        if cursor.fetchone():
            return jsonify({"message": "Profile already exists"})

        # Generate a QR token (just a placeholder format for now)
        import os
        qr_token = f"QR-{fname[0] if fname else 'X'}{lname[0] if lname else 'X'}-{os.urandom(2).hex()}"

        # Insert new profile
        cursor.execute("""
            INSERT INTO public."Profiles" (auth_id, email, fname, lname, qr_code_token)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (auth_uuid, email, fname, lname, qr_token))
        
        new_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({"message": "Profile created successfully", "profile_id": new_id})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# =====================================================
# GET CURRENT PROFILE ID
# =====================================================
@app.route("/api/my_profile_id", methods=["GET"])
def get_my_profile_id():
    user_id = get_profile_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"profile_id": user_id})

# =====================================================
# TEAM ENDPOINTS
# =====================================================
@app.route("/api/create_team", methods=["POST"])
def create_team():
    user_id = get_profile_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    name = data.get("name")
    team_size = data.get("team_size")
    description = data.get("description")
    tags = data.get("tags")

    if not name:
        return jsonify({"error": "Team name required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False

        # Check if team name already exists
        cursor.execute("""
            SELECT id FROM "Teams"
            WHERE name = %s;
        """, (name,))

        if cursor.fetchone():
            return jsonify({"error": "Team name already exists"}), 400

        # Insert new team
        cursor.execute("""
            INSERT INTO "Teams" (name, team_size, description, tags, coach_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (name, team_size, description, tags, user_id))
        
        team_id = cursor.fetchone()[0]
        
        # Add creator to user_team table (Memberships assumed based on frontend code)
        cursor.execute("""
            INSERT INTO "Memberships" (team_id, user_id)
            VALUES (%s, %s);
        """, (team_id, user_id))

        conn.commit()

        return jsonify({"message": "Team created successfully", "team_id": team_id})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/join_team", methods=["POST"])
def api_join_team_auth0():
    user_id = get_profile_id_from_token()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    team_id = data.get("team_id")

    if not team_id:
        return jsonify({"error": "Team ID required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn.autocommit = False
        
        # Check if already a member
        cursor.execute("""
            SELECT 1 FROM "Memberships"
            WHERE team_id = %s AND user_id = %s;
        """, (team_id, user_id))
        
        if cursor.fetchone():
             return jsonify({"error": "You are already in this team!"}), 400

        # Create membership
        cursor.execute("""
            INSERT INTO "Memberships" (team_id, user_id)
            VALUES (%s, %s);
        """, (team_id, user_id))

        conn.commit()

        return jsonify({"message": "Successfully joined team!"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run()