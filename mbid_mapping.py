import pandas as pd
import tarfile
import os

# --- CONFIG ---
RECCOBEATS_FILE = 'reccobeats_audio_features.csv'
DUMP_FILE = 'mbdump.tar.bz2' 
OUTPUT_MAP = 'isrc_to_mbid_map.csv'

def main():
    if not os.path.exists(DUMP_FILE):
        print(f"❌ Error: {DUMP_FILE} not found. Please wait for the download to finish.")
        return

    # 1. Load your unique ISRCs
    df_recco = pd.read_csv(RECCOBEATS_FILE)
    needed_isrcs = set(df_recco['isrc'].dropna().unique())
    print(f"🔎 Total unique ISRCs to find: {len(needed_isrcs)}")

    internal_id_to_isrc = {}
    isrc_to_mbid = {}

    with tarfile.open(DUMP_FILE, "r:bz2") as tar:
        # --- PASS 1: Map ISRC to Internal numeric Recording ID ---
        # The file is 'mbdump/recording_isrc' or sometimes 'mbdump/isrc'
        print("🚀 Pass 1/2: Scanning for ISRCs (Mapping to internal IDs)...")
        
        # We search for the member to be safe on name variations
        isrc_filename = next((m.name for m in tar.getmembers() if "recording_isrc" in m.name or m.name.endswith("/isrc")), None)
        
        if not isrc_filename:
            print("❌ Error: Could not find ISRC mapping file in dump.")
            return

        isrc_member = tar.getmember(isrc_filename)
        with tar.extractfile(isrc_member) as f:
            for line in f:
                parts = line.decode('utf-8').strip().split('\t')
                if len(parts) >= 3:
                    # In schema: [id] [recording_internal_id] [isrc_string]
                    rec_id, isrc = parts[1], parts[2]
                    if isrc in needed_isrcs:
                        internal_id_to_isrc[rec_id] = isrc
        
        print(f"✅ Found {len(internal_id_to_isrc)} numeric ID matches.")

        # --- PASS 2: Map Internal ID to the actual MBID UUID ---
        print("🚀 Pass 2/2: Mapping internal IDs to UUIDs...")
        rec_member = tar.getmember("mbdump/recording")
        with tar.extractfile(rec_member) as f:
            for line in f:
                parts = line.decode('utf-8').strip().split('\t')
                if len(parts) >= 2:
                    # [internal_id] [mbid_uuid] [name] ...
                    numeric_id, mbid = parts[0], parts[1]
                    if numeric_id in internal_id_to_isrc:
                        actual_isrc = internal_id_to_isrc[numeric_id]
                        isrc_to_mbid[actual_isrc] = mbid
                
                # Stop once we've found all possible matches
                if len(isrc_to_mbid) == len(internal_id_to_isrc):
                    break

    # 3. Save progress
    pd.DataFrame(list(isrc_to_mbid.items()), columns=['isrc', 'mbid']).to_csv(OUTPUT_MAP, index=False)
    print(f"\n🎉 SUCCESS! Mapped {len(isrc_to_mbid)} songs out of {len(needed_isrcs)} needed.")
    print(f"📁 Results saved as: {OUTPUT_MAP}")

if __name__ == "__main__":
    main()