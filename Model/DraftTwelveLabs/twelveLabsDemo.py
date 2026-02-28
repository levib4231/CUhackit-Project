
from http import client

def demo_player_recognition():
    # 1. Path to your local sample video
    video_file_path = "data/clemson_practice.mp4"
    
    # 2. Upload and Index (Direct Method)
    # We open the file in binary read mode 'rb'
    with open(video_file_path, "rb") as video_file:
        task = client.tasks.create(
            index_id="your_index_id",
            video_file=video_file # Direct local upload
        )
    
    task.wait_for_done()
    
    # 3. Identify a specific player using their Jersey + Name
    # This maps the DB 'Profile' to the visual AI search
    query = "The basketball player P.J. Hall wearing white jersey number 24 making a layup"
    
    results = client.search.query(
        index_id="your_index_id",
        query_text=query,
        options=["visual"]
    )
    
    # This prints exactly when the player was spotted
    for match in results.data:
        print(f"🎯 P.J. Hall found at {match.start}s - {match.end}s (Confidence: {match.score})")

if __name__ == "__main__":
    demo_player_recognition()