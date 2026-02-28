import os
from twelvelabs import TwelveLabs
from dotenv import load_dotenv

load_dotenv()

class TwelveLabsBranch:
    def __init__(self):
        self.client = TwelveLabs(api_key=os.getenv("TWELVELABS_API_KEY"))
        self.index_id = os.getenv("TWELVELABS_INDEX_ID")

    def upload_session_video(self, video_path, session_id):
        """
        Uploads gym footage to be indexed for a specific session.
        """
        print(f"🚀 Indexing footage for Session {session_id}...")
        task = self.client.task.create(
            index_id=self.index_id, 
            file=video_path,
            language="en"
        )
        
        # In a hackathon, we wait for completion to show the result immediately
        task.wait_for_done(sleep_interval=5)
        print(f"✅ Video indexed successfully for Session {session_id}")
        return task.id

    def find_player_highlights(self, player_name, action="making a basket"):
        """
        Uses Semantic Search to find specific player actions.
        Perfect for the Clemson Tigers Challenge.
        """
        print(f"🔍 Searching for: {player_name} {action}...")
        search_results = self.client.search.query(
            index_id=self.index_id,
            query_text=f"{player_name} {action}",
            options=["visual"]
        )
        
        # Returns timestamps and confidence scores
        return search_results.data

    def generate_player_summary(self, video_id):
        """
        Uses the 'Generate' engine to summarize the player's performance.
        """
        res = self.client.generate.summarize(
            video_id=video_id,
            type="summary"
        )
        return res.summary
    
    