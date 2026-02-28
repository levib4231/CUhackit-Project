import os
import sys
from flask import Flask, render_template, jsonify, send_from_directory, request
from dotenv import load_dotenv

# Setup Model paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Model'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Model', 'DraftTwelveLabs'))
import courtflow_backend

# Setup Flask
app = Flask(__name__, static_folder='../')

@app.route('/')
def index():
    return send_from_directory('../CUTRACKIT', 'index.html')

@app.route('/CUTRACKIT/<path:filename>')
def serve_cutrackit(filename):
    return send_from_directory('../CUTRACKIT', filename)

# Direct page routes mapping to their folders
@app.route('/dashboard')
def dashboard():
    return send_from_directory('../CUTRACKIT/Dashboard', 'index.html')

@app.route('/login')
def login():
    return send_from_directory('../CUTRACKIT/Login', 'index.html')

@app.route('/account')
def account():
    return send_from_directory('../CUTRACKIT/Account', 'account.html')

@app.route('/create_account')
def create_account():
    return send_from_directory('../CUTRACKIT/CreateAccount', 'create_account.html')

@app.route('/create_team')
def create_team():
    return send_from_directory('../CUTRACKIT/CreateTeam', 'create_team.html')

@app.route('/join_team')
def join_team():
    return send_from_directory('../CUTRACKIT/JoinTeam', 'join_team.html')

@app.route('/leaderboards')
def leaderboards():
    return send_from_directory('../CUTRACKIT/LeaderBoards', 'leaderboards.html')


# ----- API ENDPOINTS -----

@app.route('/api/dashboard_stats')
def get_dashboard_stats():
    try:
        data = courtflow_backend.get_dashboard_stats()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/active_sessions')
def get_active_sessions():
    try:
        data = courtflow_backend.get_active_sessions()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/utilization')
def get_utilization():
    try:
        data = courtflow_backend.get_utilization_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/heatmap')
def get_heatmap():
    try:
        data = courtflow_backend.get_heatmap_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    data = request.json
    qr_token = data.get('qr_token')
    court_id = data.get('court_id')
    try:
        res = courtflow_backend.check_in_player(qr_token, court_id)
        return jsonify({"message": res})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    data = request.json
    user_id = data.get('user_id')
    try:
        res = courtflow_backend.check_out_player(user_id)
        if res.get("success"):
            return jsonify({"message": "Checked out successfully"})
        else:
            return jsonify({"error": res.get("message")}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/join_team', methods=['POST'])
def api_join_team():
    data = request.json
    user_id = data.get('user_id')
    team_name = data.get('team_name')
    if not user_id or not team_name:
        return jsonify({"error": "Missing user_id or team_name"}), 400
    
    try:
        res = courtflow_backend.join_team(user_id, team_name)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Add dotenv loading from Model directory
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'Model', '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    app.run(debug=True, port=5000)