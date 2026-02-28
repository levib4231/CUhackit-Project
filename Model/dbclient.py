import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

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

# Example Usage
if __name__ == "__main__":
    active = get_active_sessions()
    print(f"Current players: {len(active)}")
    for s in active:
        print(f"- {s['Profiles']['fname']} is on {s['Courts']['name']}")

    get_dashboard_stats()