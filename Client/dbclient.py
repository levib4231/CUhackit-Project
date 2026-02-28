import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

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

def safe_check_in(user_id: int, court_id: int):
    # Call the Postgres function we just created
    response = supabase.rpc("check_in_user", {
        "p_user_id": user_id, 
        "p_court_id": court_id
    }).execute()

    result = response.data
    
    if result['success']:
        print(f"{result['message']}")
    else:
        print(f"Rejected: {result['message']}")
        
    return result

# Example Usage
if __name__ == "__main__":
    active = get_active_sessions()
    print(f"Current players: {len(active)}")
    for s in active:
        print(f"- {s['Profiles']['fname']} is on {s['Courts']['name']}")