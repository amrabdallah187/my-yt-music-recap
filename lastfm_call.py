import json
import requests
import pandas as pd
import time
import re
from tqdm import tqdm  # For the progress bar
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# 1. CONFIGURATION
# ==========================================
API_KEY = "1d4bae22ba0f5fc28055af0bed2da61a"  # Replace with your Last.fm API key
INPUT_FILE = "watch-history.json"
OUTPUT_FILE = "Song_Metadata_Detailed.csv"
MAX_WORKERS = 8

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def clean_title(title):
    if not title: return ""
    title = title.replace("Watched ", "")
    title = re.sub(r"\(.*?\)|\[.*?\]", "", title)
    garbage = ["official video", "lyrics", "audio", "official music video", "hd", "hq", "remastered", "video", "official"]
    for word in garbage:
        title = re.sub(f"(?i){word}", "", title)
    if "feat." in title.lower(): title = title.lower().split("feat.")[0]
    if "ft." in title.lower(): title = title.lower().split("ft.")[0]
    return title.strip()

def clean_artist(artist):
    if not artist: return "Unknown"
    artist = artist.replace(" - Topic", "")
    artist = re.sub(r"(?i)VEVO$", "", artist)
    return artist.strip()

def get_tags_from_response(data_obj):
    tags = data_obj.get("toptags", {}).get("tag", [])
    if not isinstance(tags, list): return "Unknown", ""
    t1 = tags[0]['name'] if len(tags) > 0 else "Unknown"
    t2 = tags[1]['name'] if len(tags) > 1 else ""
    return t1, t2

# ==========================================
# 3. THE WORKER FUNCTION (Runs in Parallel)
# ==========================================
def process_single_song(song):
    """
    This function handles ONE song entirely (Track Check -> Artist Fallback).
    It returns the dictionary result.
    """
    # Small random sleep to prevent all 8 threads from hitting the API at the exact same millisecond
    # This smoothens the traffic to avoid '429 Too Many Requests'
    time.sleep(0.1) 
    
    result = {
        "VideoID": song['VideoID'],
        "Artist": song['Artist'],
        "Title": song['Title'],
        "Genre_Primary": "Unknown",
        "Genre_Secondary": "",
        "Global_Listeners": 0,
        "Global_Playcount": 0,
        "Album": "",
        "Cover_Art": ""
    }

    try:
        # --- A. TRY TRACK INFO ---
        params = {
            "method": "track.getInfo",
            "api_key": API_KEY,
            "artist": song['Artist'],
            "track": song['Title'],
            "format": "json",
            "autocorrect": 1
        }
        # Timeout is crucial in threading so one stuck request doesn't block the pool
        resp = requests.get("http://ws.audioscrobbler.com/2.0/", params=params, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if "track" in data:
                track = data['track']
                result['Genre_Primary'], result['Genre_Secondary'] = get_tags_from_response(track)
                result['Global_Listeners'] = track.get("listeners", 0)
                result['Global_Playcount'] = track.get("playcount", 0)
                result['Album'] = track.get("album", {}).get("title", "")
                images = track.get("album", {}).get("image", [])
                result['Cover_Art'] = images[3]['#text'] if len(images) > 3 else ""

        # --- B. ARTIST FALLBACK (If Track Genre is Unknown) ---
        if result['Genre_Primary'] == "Unknown" and song['Artist'] != "Unknown":
            params_art = {
                "method": "artist.getTopTags",
                "api_key": API_KEY,
                "artist": song['Artist'],
                "format": "json",
                "autocorrect": 1
            }
            resp_art = requests.get("http://ws.audioscrobbler.com/2.0/", params=params_art, timeout=10)
            if resp_art.status_code == 200:
                data_art = resp_art.json()
                if "toptags" in data_art:
                    result['Genre_Primary'], result['Genre_Secondary'] = get_tags_from_response(data_art)

    except Exception as e:
        # In threading, print() can get messy, so we just pass or log silently
        pass

    return result

# ==========================================
# 4. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("Loading JSON...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        history_data = json.load(f)

    unique_songs = {}
    print("Preparing song list...")
    
    # Pre-processing loop (Still single threaded, but fast)
    for entry in history_data:
        if entry.get("header") != "YouTube Music": continue
        url = entry.get("titleUrl", "")
        if "watch?v=" not in url: continue
        video_id = url.split("v=")[1]
        
        if "subtitles" in entry and len(entry["subtitles"]) > 0:
            clean_artist_name = clean_artist(entry["subtitles"][0].get("name"))
            clean_track_name = clean_title(entry.get("title", ""))
            
            unique_songs[video_id] = {
                "VideoID": video_id,
                "Artist": clean_artist_name,
                "Title": clean_track_name
            }

    song_list = list(unique_songs.values())
    print(f"Starting Multi-threaded Processing for {len(song_list)} songs...")
    print(f"Workers: {MAX_WORKERS}")

    results = []
    
    # ThreadPoolExecutor Magic
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        # tqdm wraps the iterator to show a progress bar
        futures = list(tqdm(executor.map(process_single_song, song_list), total=len(song_list)))
        
        # Collect results
        results = list(futures)

    # Save
    print("Saving to CSV...")
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Done! Saved to {OUTPUT_FILE}")