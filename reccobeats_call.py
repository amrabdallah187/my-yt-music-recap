import csv
import time
import requests
import math
import sys

# --- CONFIGURATION ---
INPUT_FILE = 'enriched_history.csv'       # Your input file
OUTPUT_FILE = 'reccobeats_audio_features.csv'
ID_COLUMN = 'spotify_id'             # The column header for IDs in your CSV

# ⚠️ DOCUMENTATION CONSTRAINT: "Possible values: >= 1, <= 40"
BATCH_SIZE = 40 

HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def fetch_batch_strict(id_list):
    """
    Fetches features for a batch of IDs adhering strictly to ReccoBeats docs.
    Endpoint: GET https://api.reccobeats.com/v1/audio-features
    Param: ids (comma separated string)
    """
    # Join IDs with commas
    ids_param = ",".join(id_list)
    
    # We use params dict to ensure correct URL encoding
    params = {'ids': ids_param}
    url = "https://api.reccobeats.com/v1/audio-features"
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            
            # ⚠️ DOCS FIX: Response schema is { "content": [ ... ] }
            if 'content' in data:
                return data['content']
            # Fallback if API changes, but docs say 'content'
            elif isinstance(data, list): 
                return data
            else:
                return []
                
        elif response.status_code == 429:
            print("   [!] Rate limit (429). Sleeping 5s...")
            time.sleep(5)
            return fetch_batch_strict(id_list)
        else:
            print(f"   [!] Error {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        print(f"   [!] Connection Error: {e}")
        return []

def main():
    print(f"📖 Reading {INPUT_FILE}...")
    
    all_ids = []
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f: # utf-8-sig handles BOM
            reader = csv.DictReader(f)
            # Clean headers just in case
            reader.fieldnames = [h.strip() for h in reader.fieldnames]
            
            if ID_COLUMN not in reader.fieldnames:
                print(f"❌ Error: Column '{ID_COLUMN}' not found.")
                print(f"   Found columns: {reader.fieldnames}")
                return
            
            for row in reader:
                val = row.get(ID_COLUMN, '').strip()
                if val:
                    all_ids.append(val)
    except FileNotFoundError:
        print(f"❌ Error: File '{INPUT_FILE}' not found.")
        return

    total_songs = len(all_ids)
    print(f"✅ Loaded {total_songs} IDs.")

    # Prepare Output
    # Fields based on ReccoBeats Documentation
    csv_headers = [
        'id', 'tempo', 'key', 'mode', 'energy', 'danceability', 
        'valence', 'acousticness', 'instrumentalness', 'liveness', 
        'speechiness', 'loudness', 'isrc', 'href'
    ]

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()

        # Batch Processing
        total_batches = math.ceil(total_songs / BATCH_SIZE)
        
        for i in range(0, total_songs, BATCH_SIZE):
            batch_ids = all_ids[i : i + BATCH_SIZE]
            current_batch = (i // BATCH_SIZE) + 1
            
            print(f"Processing Batch {current_batch}/{total_batches} ({len(batch_ids)} songs)...")
            
            features_list = fetch_batch_strict(batch_ids)
            
            success_count = 0
            if features_list:
                for feat in features_list:
                    if feat:
                        writer.writerow({
                            'id': feat.get('id'),
                            'tempo': feat.get('tempo'),
                            'key': feat.get('key'),
                            'mode': feat.get('mode'),
                            'energy': feat.get('energy'),
                            'danceability': feat.get('danceability'),
                            'valence': feat.get('valence'),
                            'acousticness': feat.get('acousticness'),
                            'instrumentalness': feat.get('instrumentalness'),
                            'liveness': feat.get('liveness'),
                            'speechiness': feat.get('speechiness'),
                            'loudness': feat.get('loudness'),
                            'isrc': feat.get('isrc'),
                            'href': feat.get('href')
                        })
                        success_count += 1
            
            print(f"   -> Saved {success_count} features.")
            
            # Politeness delay
            time.sleep(0.2)

    print(f"\n🎉 Done! Data saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()