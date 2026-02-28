import yt_dlp
import os

def download_clemson_highlights():
    # The clip featuring P.J. Hall and Chase Hunter
    url = "https://www.youtube.com/watch?v=v0Icvb6IAyA"
    
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'data/clemson_demo.%(ext)s',  # Saves as data/clemson_demo.mp4
        'noplaylist': True,
    }

    print(f"🏀 Downloading Clemson highlights for TwelveLabs demo...")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"✅ Download complete! File located at: data/clemson_demo.mp4")
    except Exception as e:
        print(f"❌ Error downloading: {e}")

if __name__ == "__main__":
    download_clemson_highlights()