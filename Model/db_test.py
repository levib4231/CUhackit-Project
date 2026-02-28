import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
#env_path = Path(__file__).parent / '.env' dotenv_path=env_path
load_dotenv()

def test_db_connection():
    try:
        # Pulling from your .env
        connection = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            port=os.environ.get("DB_PORT")
        )

        cursor = connection.cursor()
        
        # Execute a simple query to verify connection
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print("Connection Successful!")
        print(f"Database version: {db_version[0]}")
        
        # Verify the 'Profiles' table exists
        cursor.execute("SELECT count(*) FROM \"Profiles\";")
        profile_count = cursor.fetchone()[0]
        print(f"Profile Count: {profile_count}")

        cursor.close()
        connection.close()

    except Exception as error:
        print(f"Connection Failed: {error}")
        print("\nTroubleshooting Tips:")
        print("1. Check if your IP is allowed in Supabase (Settings > Database > Network Restrictions).")
        print("2. Ensure your password doesn't have special characters that need URL encoding.")
        print("3. Verify the Port is 5432 (Direct) or 6543 (Pooled).")

if __name__ == "__main__":
    test_db_connection()