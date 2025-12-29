import json
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import time
import os

# --- CONFIGURATION ---
INPUT_FILE = 'watch-history.json'
OUTPUT_FILE = 'enriched_history.csv'
# ---------------------

def setup_spotify():
    load_dotenv()
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Error: API keys not found in .env file.")
        exit()
        
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)

def clean_title(text):
    """Specifically cleans the Title field"""
    if not isinstance(text, str): return ""
    
    # 1. Remove the "Watched " prefix (CRITICAL FIX based on your JSON)
    if text.startswith("Watched "):
        text = text.replace("Watched ", "", 1)
        
    # 2. Remove standard junk
    replacements = ["(Official Video)", "(Official Audio)", "(Lyrics)", 
                    "(Official Music Video)", "[Official Video]", 
                    "ft.", "feat.", "(Remaster)", "(Stereo Remix)"]
    for r in replacements:
        text = text.replace(r, "")
        
    return text.strip()

def clean_artist(text):
    """Specifically cleans the Artist field"""
    if not isinstance(text, str): return ""
    # Remove " - Topic" which appears in your JSON
    return text.replace(" - Topic", "").strip()

def main():
    sp = setup_spotify()
    
    print(f"📂 Reading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find '{INPUT_FILE}'.")
        return

    # --- PHASE 1: PARSE JSON ---
    print("   Parsing JSON and cleaning titles...")
    rows = []
    
    for item in data:
        # Filter: Only keep YouTube Music entries
        if item.get('header') == 'YouTube Music':
            raw_title = item.get('title', '')
            
            # Extract Artist safely
            try:
                raw_artist = item['subtitles'][0]['name']
            except (KeyError, IndexError, TypeError):
                raw_artist = ""

            # APPLY CLEANING
            clean_t = clean_title(raw_title)
            clean_a = clean_artist(raw_artist)

            if clean_t: # Only add if we have a title
                rows.append({
                    'timestamp': item['time'],
                    'title': clean_t,
                    'artist': clean_a,
                    'original_title': raw_title # Keep strictly for debugging
                })
    
    df = pd.DataFrame(rows)
    print(f"🎵 Found {len(df)} history entries.")
    
    # --- PHASE 2: DEDUPLICATE & SEARCH ---
    # We create a list of UNIQUE songs so we don't search the same song 100 times
    unique_songs = df[['title', 'artist']].drop_duplicates()
    unique_songs = unique_songs.reset_index(drop=True)
    unique_songs['spotify_id'] = None
    
    print(f"   Identified {len(unique_songs)} UNIQUE songs to search.")
    print("🚀 Finding Spotify IDs...")
    
    for index, row in unique_songs.iterrows():
        query = f"track:{row['title']} artist:{row['artist']}"
        
        try:
            # Search Spotify
            results = sp.search(q=query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                unique_songs.at[index, 'spotify_id'] = track['id']
                unique_songs.at[index, 'spotify_name'] = track['name'] # Verify match later
            
        except Exception as e:
            print(f"   ❌ Error searching '{row['title']}': {e}")
            time.sleep(2)
            
        # Progress bar logic
        if index % 10 == 0:
            print(f"   ...Searched {index}/{len(unique_songs)} songs", end='\r')
            time.sleep(0.1)

    # --- PHASE 3: FETCH AUDIO FEATURES ---
    print("\n🔬 Fetching Audio Features (Danceability, Energy, Time Signature)...")
    
    # Only get features for songs we actually found
    found_df = unique_songs[unique_songs['spotify_id'].notnull()]
    track_ids = found_df['spotify_id'].tolist()
    
    # Map to store the results: {spotify_id: {data}}
    features_map = {}
    
    chunk_size = 50
    for i in range(0, len(track_ids), chunk_size):
        chunk = track_ids[i:i + chunk_size]
        try:
            features_list = sp.audio_features(chunk)
            for feat in features_list:
                if feat:
                    features_map[feat['id']] = feat
            
            print(f"   Processed batch {i}...", end='\r')
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Batch Error: {e}")

    # --- PHASE 4: MERGE & SAVE ---
    print("\n🔄 Merging everything back to the original timestamps...")
    
    # 1. Attach features to the unique song list
    for pid, feats in features_map.items():
        mask = unique_songs['spotify_id'] == pid
        for key, value in feats.items():
             if key not in ['type', 'id', 'uri', 'track_href', 'analysis_url']:
                unique_songs.loc[mask, key] = value
                
    # 2. Merge unique songs back to the main history DataFrame
    # This aligns the features with every single timestamp you listened
    final_df = pd.merge(df, unique_songs, on=['title', 'artist'], how='left')

    print(f"💾 Saving {len(final_df)} rows to {OUTPUT_FILE}...")
    final_df.to_csv(OUTPUT_FILE, index=False)
    print("🎉 Done! Open 'enriched_history.csv' in Power BI.")

if __name__ == "__main__":
    main()