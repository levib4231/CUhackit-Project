import os
from flask import Flask, render_template, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Setup
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'Model', '.env')
load_dotenv(dotenv_path=dotenv_path)
app = Flask(__name__)

# 2. Supabase Connection
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    """Serves the main dashboard page."""
    return render_template('index.html')

@app.route('/api/courts')
def get_courts():
    """API endpoint for the frontend to fetch court data."""
    try:
        response = supabase.table("Courts").select("*").execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Flask runs on port 5000 by default
    app.run(debug=True, port=5000)