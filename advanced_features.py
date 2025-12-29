import csv
import requests
import time
import pandas as pd
import os

# --- CONFIG ---
MAP_FILE = 'isrc_to_mbid_map.csv' 
OUTPUT_FILE = 'acoustic_final_data.csv'
BATCH_SIZE = 25 
HEADERS = {'User-Agent': 'MyMusicProject/5.0 (amrahmedabdallah12@gmail.com)'}

def fetch_acousticbrainz(mbid_list):
    ids_param = ";".join(mbid_list)
    results = {}
    for level in ['low-level', 'high-level']:
        url = f"https://acousticbrainz.org/api/v1/{level}"
        try:
            res = requests.get(url, params={'recording_ids': ids_param, 'map_classes': 'true'}, headers=HEADERS, timeout=30)
            if res.status_code == 200:
                results[level] = res.json()
        except:
            continue
    return results

def main():
    if not os.path.exists(MAP_FILE):
        print(f"❌ Error: {MAP_FILE} not found. Run the offline mapper first!")
        return

    map_df = pd.read_csv(MAP_FILE)
    unique_mbids = map_df['mbid'].unique().tolist()
    
    # --- RESUME LOGIC ---
    existing_mbids = set()
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE)
        existing_mbids = set(existing_df['mbid'].astype(str).unique())
    
    to_fetch = [m for m in unique_mbids if str(m) not in existing_mbids]
    print(f"✅ Total: {len(unique_mbids)} | Already Done: {len(existing_mbids)} | Remaining: {len(to_fetch)}")

    fieldnames = [
        'mbid', 'duration_sec', 'bpm', 'beats_count', 'danceability_prob', 
        'genre_rosamerica', 'genre_dortmund', 'genre_electronic', 'genre_tzanetakis',
        'mood_happy', 'mood_sad', 'mood_acoustic', 'mood_aggressive', 'mood_relaxed',
        'mood_party', 'mood_electronic', 'voice_instrumental', 'gender',
        'key_key', 'key_scale', 'key_strength', 'chords_key', 'chords_scale', 'chords_changes_rate'
    ]

    # Open in 'a' (append) mode
    file_exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for i in range(0, len(to_fetch), BATCH_SIZE):
            batch = to_fetch[i : i + BATCH_SIZE]
            print(f"📡 Progress: {i + len(existing_mbids)}/{len(unique_mbids)} ...", end='\r')
            
            data = fetch_acousticbrainz(batch)
            
            for mbid in batch:
                ll = data.get('low-level', {}).get(mbid, {}).get('0', {})
                hl = data.get('high-level', {}).get(mbid, {}).get('0', {})
                
                if not ll and not hl:
                    continue

                writer.writerow({
                    'mbid': mbid,
                    'duration_sec': ll.get('metadata', {}).get('audio_properties', {}).get('length'),
                    'bpm': ll.get('rhythm', {}).get('bpm'),
                    'beats_count': ll.get('rhythm', {}).get('beats_count'), # Raw count only
                    
                    # High Level - Genres
                    'genre_rosamerica': hl.get('highlevel', {}).get('genre_rosamerica', {}).get('value'),
                    'genre_dortmund': hl.get('highlevel', {}).get('genre_dortmund', {}).get('value'),
                    'genre_electronic': hl.get('highlevel', {}).get('genre_electronic', {}).get('value'),
                    'genre_tzanetakis': hl.get('highlevel', {}).get('genre_tzanetakis', {}).get('value'),
                    
                    # High Level - Moods
                    'danceability_prob': hl.get('highlevel', {}).get('danceability', {}).get('probability'),
                    'mood_happy': hl.get('highlevel', {}).get('mood_happy', {}).get('probability'),
                    'mood_sad': hl.get('highlevel', {}).get('mood_sad', {}).get('probability'),
                    'mood_acoustic': hl.get('highlevel', {}).get('mood_acoustic', {}).get('probability'),
                    'mood_aggressive': hl.get('highlevel', {}).get('mood_aggressive', {}).get('probability'),
                    'mood_relaxed': hl.get('highlevel', {}).get('mood_relaxed', {}).get('probability'),
                    'mood_party': hl.get('highlevel', {}).get('mood_party', {}).get('probability'),
                    'mood_electronic': hl.get('highlevel', {}).get('mood_electronic', {}).get('probability'),
                    'voice_instrumental': hl.get('highlevel', {}).get('voice_instrumental', {}).get('value'),
                    'gender': hl.get('highlevel', {}).get('gender', {}).get('value'),
                    
                    # Low Level - Tonal
                    'key_key': ll.get('tonal', {}).get('key_key'),
                    'key_scale': ll.get('tonal', {}).get('key_scale'),
                    'key_strength': ll.get('tonal', {}).get('key_strength'),
                    'chords_key': ll.get('tonal', {}).get('chords_key'),
                    'chords_scale': ll.get('tonal', {}).get('chords_scale'),
                    'chords_changes_rate': ll.get('tonal', {}).get('chords_changes_rate')
                })
            
            time.sleep(1.0)

    print(f"\n🎉 Done! Full musical profile saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()