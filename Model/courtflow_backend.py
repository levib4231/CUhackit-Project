"""
CourtFlow Backend

This file handles:
1. Registering a player to a court (check-in)
2. Checking a player out
3. Getting live court occupancy
4. Updating court status automatically

Features:
- JWT authentication
- Prevent double check-in
- Prevent race conditions (transaction locking)
- Auto timeout cleanup
- Live player list
- Supabase PostgreSQL connection
"""

# Imports
from multiprocessing.connection import Client
from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# =====================================================
# SUPABASE DATABASE CONNECTION (ENV VARIABLES REQUIRED)
# =====================================================

# The code retrieves the Supabase URL and API key from environment variables and creates a Supabase client instance. This client can be used to interact with the Supabase database, although in this implementation, we are using psycopg2 for direct PostgreSQL connections instead of the Supabase client for database operations. The environment variables SUPABASE_URL and SUPABASE_KEY must be set in the .env file for this to work properly.
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# The DB_CONFIG dictionary is defined to hold the database connection parameters (host, database name, user, password, and port) that are retrieved from environment variables. This configuration is used by the get_db_connection() function to establish a connection to the PostgreSQL database whenever a request is made to the API endpoints.
DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "database": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "port": os.environ.get("DB_PORT")
}

# The JWT_SECRET variable is defined to hold the secret key used for encoding and decoding JWT tokens. This secret key must be kept secure and should be set in the environment variables for the application to function properly. It is used in the verify_jwt function to validate incoming JWT tokens and extract the user_id from them.
JWT_SECRET = os.environ.get("JWT_SECRET")


# get_db_connection() returns a new connection to the PostgreSQL database using the credentials defined in the environment variables. Each time this function is called, it creates a new connection that can be used to execute SQL queries. This is important for handling multiple requests concurrently without sharing connections between them, which can lead to issues.
def get_db_connection():
    """
    Opens new database connection for each request.
    """
    return psycopg2.connect(**DB_CONFIG)


# =====================================================
# JWT AUTHENTICATION HELPER
# =====================================================

# verify_jwt(token) takes a JWT token as input, decodes it using the secret key, and returns the user_id if the token is valid. If the token is expired or invalid, it returns None with an error message. This function is used to authenticate users based on the JWT they provide in the Authorization header of their requests.
def verify_jwt(token):
    """
    Verifies JWT and extracts user_id.
    """
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded.get("user_id")
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None


# get_user_from_request() reads the Authorization header from the incoming HTTP request, extracts the JWT token, and uses the verify_jwt function to decode it and retrieve the user_id. If the header is missing or the token is invalid, it returns None with an error message. This function is used in the check-in and check-out endpoints to identify which user is making the request.
def get_user_from_request():
    """
    Extracts JWT from Authorization header.
    Header must be:
    Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization")

    # If the authorization header is missing from the incoming request, the function prints an error message indicating that the header is missing and returns None. This check ensures that the function does not attempt to process a request that does not contain the necessary authentication information, which helps prevent unauthorized access to the API endpoints.
    if not auth_header:
        print("Authorization header missing")
        return None

    # The function then attempts to split the Authorization header to extract the token
    try:
        token = auth_header.split(" ")[1]
        print(f"Extracted token: {token}")
        return verify_jwt(token)
    except:
        print("Invalid Authorization header format")
        return None


# =====================================================
# AUTO CLEANUP (2 HOUR TIMEOUT)
# =====================================================

# cleanup_expired_sessions(cursor) is a helper function that updates the "Sessions" table to set the check_out_at timestamp to the current time for any sessions that have been active for more than 2 hours. This is done to automatically free up court spots for users who may have forgotten to check out or left without doing so. This function is called at the beginning of each endpoint to ensure that the court occupancy data is accurate and up-to-date.
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

# The /checkin endpoint allows a user to check into a court.
# Steps:
# 1. It first verifies the user's JWT to ensure they are authenticated.
# 2. It retrieves the court_id from the request body.
# 3. It starts a database transaction to ensure data integrity.
# 4. It cleans up any expired sessions to free up court spots.
# 5. It checks if the user is already checked into a court to prevent double check-ins.
# 6. It locks the court row to prevent race conditions.
@app.route("/checkin", methods=["POST"])
def check_in():

    # Step 1: Authenticate user using JWT
    user_id = get_user_from_request()

    # If the user is not authenticated (i.e., no valid JWT is provided), the endpoint responds with a 401 error and a message indicating that the user is unauthorized. This ensures that only authenticated users can check into a court, protecting the system from unauthorized access.
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Step 2: Get court_id from request body
    data = request.get_json()
    court_id = data.get("court_id")

    # If the court_id is not provided in the request body, the endpoint responds with a 400 error and a message indicating that the court_id is required. This ensures that clients provide the necessary information to check into a court and prevents processing incomplete requests.
    if not court_id:
        return jsonify({"error": "court_id required"}), 400

    # Step 3: Start database transaction
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # 4-6: Cleanup expired sessions, check for double check-in, lock court row, and insert new session
    try:
        # Start transaction
        conn.autocommit = False

        # Cleanup expired sessions (auto timeout)
        cleanup_expired_sessions(cursor)

        # It then checks the "Sessions" table to see if the user is already checked into a court (i.e., has an active session with check_out_at as NULL). If they are, it returns an error to prevent double check-ins.
        # Prevent double check-in
        cursor.execute("""
            SELECT 1 FROM "Sessions"
            WHERE user_id = %s
            AND check_out_at IS NULL;
        """, (user_id,))
        if cursor.fetchone():
            return jsonify({"error": "Already checked into a court"}), 400

        # Lock court row (prevents race condition)
        cursor.execute("""
            SELECT max_capacity
            FROM "Courts"
            WHERE id = %s
            FOR UPDATE;
        """, (court_id,))
        court = cursor.fetchone()

        # If the court with the specified court_id does not exist in the "Courts" table, the query will return None. In this case, the endpoint responds with a 404 error and a message indicating that the court was not found. This ensures that clients receive appropriate feedback when trying to check into a non-existent court.
        if not court:
            return jsonify({"error": "Court not found"}), 404

        # update max_capacity variable to use the value from the database instead of hardcoding it
        max_capacity = court["max_capacity"]

        # Count active players
        cursor.execute("""
            SELECT COUNT(*) FROM "Sessions"
            WHERE court_id = %s
            AND check_out_at IS NULL;
        """, (court_id,))
        current_players = cursor.fetchone()[0]

        # If the current number of players checked into the court is greater than or equal to the max_capacity, it returns an error indicating that the court is full. This check ensures that the system enforces the maximum capacity limit for each court and prevents overbooking.
        if current_players >= max_capacity:
            return jsonify({"error": "Court is full"}), 403

        # Insert new session
        cursor.execute("""
            INSERT INTO "Sessions" (user_id, court_id)
            VALUES (%s, %s);
        """, (user_id, court_id))

        # Update court status
        new_count = current_players + 1
        status = "Full" if new_count >= max_capacity else "Open"

        # Update the "Courts" table to set the new status for the court that the user checked into. This ensures that the court's status is updated in the database so that it can be reflected in future queries about the court's occupancy and status.
        cursor.execute("""
            UPDATE "Courts"
            SET status = %s
            WHERE id = %s;
        """, (status, court_id))

        # Commit transaction
        conn.commit()

        # Return success response with current player count and court status
        return jsonify({
            "message": "Checked in successfully",
            "current_players": new_count,
            "max_capacity": max_capacity,
            "status": status
        })

    # If any error occurs during the transaction (e.g., database errors, integrity issues), it rolls back the transaction to maintain data integrity and returns an error response with the exception message.
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    # its important to close the cursor and connection in a finally block to ensure that resources are released properly, even if an error occurs during the transaction. This prevents potential memory leaks and ensures that database connections are not left open unintentionally.
    finally:
        cursor.close()
        conn.close()


# =====================================================
# CHECK-OUT ENDPOINT
# =====================================================


# The /checkout endpoint allows a user to check out of a court. It performs the following steps:
# 1. It verifies the user's JWT to ensure they are authenticated.
# 2. It starts a database transaction to ensure data integrity.
# 3. It updates the "Sessions" table to set the check_out_at timestamp to the current time for the user's active session (where check_out_at is NULL).
# 4. It retrieves the court_id from the updated session to identify which court the user was checked into.
# 5. It counts the remaining active sessions for that court to determine how many players are still checked in.
# 6. It retrieves the max_capacity for the court from the "Courts" table.
# 7. It updates the court's status to "Full" if the remaining active sessions are greater than or equal to max_capacity, or "Open" if there are fewer active sessions than max_capacity.
@app.route("/checkout", methods=["POST"])
def check_out():

    # 1: Authenticate user using JWT
    user_id = get_user_from_request()

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # 2: Start database transaction
    conn = get_db_connection()
    cursor = conn.cursor()

    # 3-7: Update session, get court_id, count remaining players, get max_capacity, and update court status
    try:
        conn.autocommit = False

        # This query updates the "Sessions" table to set the check_out_at timestamp to the current time for the session where the user_id matches and check_out_at is NULL (indicating an active session). It also returns the court_id of the session that was updated, which is needed to update the court status later.
        cursor.execute("""
            UPDATE "Sessions"
            SET check_out_at = NOW()
            WHERE user_id = %s
            AND check_out_at IS NULL
            RETURNING court_id;
        """, (user_id,))

        # 4: Get court_id from the updated session
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "No active session"}), 404

        # Extract court_id from the result of the UPDATE query. This is necessary to identify which court the user was checked into, so that we can update the court's status based on the remaining active sessions.
        court_id = result[0]

        # Update court status after checkout
        cursor.execute("""
            SELECT COUNT(*) FROM "Sessions"
            WHERE court_id = %s
            AND check_out_at IS NULL;
        """, (court_id,))
        remaining = cursor.fetchone()[0]

        # Retrieve max_capacity for the court to determine if it should be marked as "Full" or "Open". This ensures that the court status is accurately updated based on the current occupancy after the user checks out.
        cursor.execute("""
            SELECT max_capacity FROM "Courts"
            WHERE id = %s;
        """, (court_id,))
        max_capacity = cursor.fetchone()[0]

        # Update court status based on remaining active sessions compared to max_capacity. If the number of remaining active sessions is greater than or equal to max_capacity, the court is marked as "Full". Otherwise, it is marked as "Open". This logic ensures that the court status reflects the current occupancy accurately.
        status = "Full" if remaining >= max_capacity else "Open"

        # Update the "Courts" table to set the new status for the court that the user checked out of. This ensures that the court's status is updated in the database so that it can be reflected in future queries about the court's occupancy and status.
        cursor.execute("""
            UPDATE "Courts"
            SET status = %s
            WHERE id = %s;
        """, (status, court_id))

        conn.commit()

        return jsonify({"message": "Checked out successfully"})

    # If any error occurs during the transaction (e.g., database errors, integrity issues), it rolls back the transaction to maintain data integrity and returns an error response with the exception message. This ensures that if something goes wrong during the check-out process, the database state remains consistent and the user receives feedback about the error that occurred.
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =====================================================
# GET COURT STATUS + PLAYER LIST
# =====================================================

# The /court/<int:court_id> endpoint allows clients to retrieve the current status of a specific court, including the list of players currently checked in. It performs the following steps:
# 1. It starts a database connection and cursor.
# 2. It calls the cleanup_expired_sessions function to ensure that any sessions that have been active for more than 2 hours are marked as checked out, which helps maintain accurate court occupancy data.
# 3. It queries the "Courts" table to retrieve the name, max_capacity, and status of the specified court using the court_id from the URL parameter. If the court is not found, it returns a 404 error.
# 4. It queries the "Sessions" table joined with the "Profiles" table to retrieve the first name and last name of all players currently checked into the specified court (where check_out_at is NULL).
# 5. It constructs a list of players and returns a JSON response containing the court's name, status, max_capacity, current player count, and the list of players currently checked in.
@app.route("/court/<int:court_id>", methods=["GET"])
def get_court_status(court_id):

    # 1: Start database connection and cursor
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # 2-5: Cleanup expired sessions, get court info, get current players, and return response
    try:
        # 2: Cleanup expired sessions to ensure accurate court occupancy data. This step is important to automatically free up court spots for users who may have forgotten to check out or left without doing so, ensuring that the information returned about the court's status and current players is up-to-date.
        cleanup_expired_sessions(cursor)

        # 3: Query the "Courts" table to retrieve the name, max_capacity, and status of the specified court using the court_id from the URL parameter. If the court is not found, it returns a 404 error. This step ensures that the client receives accurate information about the court's details and status.
        cursor.execute("""
            SELECT name, max_capacity, status
            FROM "Courts"
            WHERE id = %s;
        """, (court_id,))
        court = cursor.fetchone()

        # If the court with the specified court_id does not exist in the "Courts" table, the query will return None. In this case, the endpoint responds with a 404 error and a message indicating that the court was not found. This ensures that clients receive appropriate feedback when requesting information about a non-existent court.
        if not court:
            return jsonify({"error": "Court not found"}), 404

        # 4: Query the "Sessions" table joined with the "Profiles" table to retrieve the first name and last name of all players currently checked into the specified court (where check_out_at is NULL). This step allows the client to see who is currently using the court, providing a live player list for that court.
        cursor.execute("""
            SELECT p.fname, p.lname
            FROM "Sessions" s
            JOIN "Profiles" p ON s.user_id = p.id
            WHERE s.court_id = %s
            AND s.check_out_at IS NULL;
        """, (court_id,))
        players = cursor.fetchall()

        # 5: Construct a list of players and return a JSON response containing the court's name, status, max_capacity, current player count, and the list of players currently checked in. This provides the client with comprehensive information about the court's current state and occupancy. The player list is formatted as a list of dictionaries, each containing the first name and last name of a player currently checked in.
        player_list = [
            {"fname": p["fname"], "lname": p["lname"]}
            for p in players
        ]

        # The response includes the court's name, current status (e.g., "Open" or "Full"), maximum capacity, the current number of players checked in, and a list of the players currently using the court. This allows clients to easily display the court's status and occupancy information in the frontend application.
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

# The if __name__ == "__main__": block checks if the script is being run directly (as the main program) rather than imported as a module. If it is being run directly, it calls app.run() to start the Flask development server, allowing the API to be accessible for handling incoming HTTP requests. This is a common pattern in Flask applications to ensure that the server only starts when the script is executed directly, and not when it is imported by another module.
if __name__ == "__main__":
    app.run()