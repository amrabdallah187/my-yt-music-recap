# YouTube Music Audio Feature Extractor & Analyzer

A complete data pipeline that extracts your YouTube Music listening history, enriches it with Spotify metadata, fetches advanced audio telemetry (BPM, Energy, Key), and uses **AcousticBrainz AI** for deep rhythmic and mood analysis.

## 📋 Project Overview

This toolset transforms your raw Google Takeout data into a rich dataset. It maps your YouTube Music history to Spotify IDs, uses the ReccoBeats API to fetch standard audio metrics, and bridges to the open-source MusicBrainz database for deep AI modeling.

**The Pipeline:**
1.  **Deduplicate & Search:** `myrecap.py` cleans your history and finds corresponding Spotify IDs.
2.  **Batch Fetch Telemetry:** `reccobeats_call.py` fetches advanced metrics (Tempo, Valence, Liveness, etc.) using a 40-song batch limit.
3.  **Map to MusicBrainz:** `mbid_mapping.py` uses a local database dump to link your songs to MusicBrainz IDs (MBIDs) via their ISRC.
4.  **Deep AI Analysis:** `advanced_features.py` queries AcousticBrainz for high-level (Mood, Genre) and low-level (Rhythm, Tonal) data.
5.  **Analyze & Clean:** The output is ready for Power BI, Tableau, or Excel for further filtering and visualization.

## 🛠️ Prerequisites

* **Python 3.13+**
* **Spotify Developer Account:** To obtain a Client ID & Secret.
* **Google Takeout:** Your `watch-history.json` file.
* **MusicBrainz Database Dump:** You need the `mbdump.tar.bz2` (~6GB) from [MusicBrainz Data Dumps](https://data.metabrainz.org/pub/musicbrainz/data/fullexport/) to run Step 3.

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/amrabdallah187/my-yt-music-recap.git
    cd my-yt-music-recap
    ```

2.  **Install dependencies:**
    ```bash
    pip install pandas spotipy requests python-dotenv
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root folder:
    ```ini
    SPOTIPY_CLIENT_ID='your_client_id_here'
    SPOTIPY_CLIENT_SECRET='your_client_secret_here'
    ```

## 🚀 Usage Guide

### Step 1: Resolve Spotify IDs
Run the enrichment script to parse your history and identify unique Spotify IDs.
* **Input:** `watch-history.json`
* **Output:** `enriched_history.csv`

```bash
python myrecap.py

```

### Step 2: Fetch Audio Features

Run the fetcher to get audio metrics from the ReccoBeats API. This script is optimized for the strict 40-song batch limit.

* **Input:** `enriched_history.csv`
* **Output:** `reccobeats_audio_features.csv`

```bash
python reccobeats_call.py

```

### Step 3: Map to MusicBrainz (The Bridge)

Scans the local MusicBrainz database dump to find the MBID for every song via its ISRC.

* **Input:** `mbdump.tar.bz2` (Must be in root folder)
* **Run:** `python mbid_mapping.py`
* **Output:** `isrc_to_mbid_map.csv`

### Step 4: Fetch Advanced Acoustic Data

Queries the AcousticBrainz API for high-level and low-level descriptors.

* **Input:** `isrc_to_mbid_map.csv`
* **Run:** `python advanced_features.py`
* **Output:** `acoustic_final_data.csv`

### Step 5: Analysis & Visualization

The final CSV files are structured for easy import into Business Intelligence tools.

* **Cleaning:** You can perform further data cleaning directly within **Power BI (Power Query)**, **Excel**, or **Tableau**.
* **Analysis:** Use the audio metrics to find patterns in your mood, energy levels, or rhythmic complexity (Prog/Jazz detection).

## 📂 File Structure

| File | Description |
| --- | --- |
| `myrecap.py` | Cleans raw YouTube data, handles Spotify ID resolution, and saves the history. |
| `reccobeats_call.py` | Specifically fetches audio features from ReccoBeats in batches of 40. |
| `mbid_mapping.py` | Maps ISRCs to MusicBrainz IDs using local dump. |
| `advanced_features.py` | Fetches deep acoustic data (Beats, Chords, Mood) from AcousticBrainz. |

## 📊 Data Points

The final dataset includes the following metrics, which can be used to filter and categorize your music history:

### 🟢 Basic Telemetry (Spotify/ReccoBeats)

* **Timestamp:** The exact date and time the track was played.
* **Artist:** The name of the performing artist or band.
* **Title:** The original track title as recorded in your YouTube Music history.
* **Spotify Name:** The standardized track name found on Spotify.
* **Valence (Happiness):** (0.0 - 1.0) Measures the emotional tone. High = happy, Low = sad/angry.
* **Energy:** (0.0 - 1.0) Represents intensity. High-energy tracks feel fast, loud, and noisy (e.g., death metal).
* **Danceability:** (0.0 - 1.0) Suitability for dancing based on tempo, rhythm stability, and beat strength.
* **Tempo:** The overall estimated tempo of a track in beats per minute (BPM).
* **Key & Mode:** Musical key (C, C#) and modality (Major = 1, Minor = 0).
* **Loudness:** The overall loudness of a track in decibels (dB).
* **Acousticness:** (0.0 - 1.0) Confidence measure of whether the track is acoustic vs electronic.
* **Instrumentalness:** (0.0 - 1.0) Likelihood the track contains no vocals.
* **Liveness:** (0.0 - 1.0) Detects the presence of an audience (Live performance).
* **Speechiness:** (0.0 - 1.0) Detects the presence of spoken words (Podcasts/Rap).
* **ID & Metadata:** Spotify ID, ISRC, and Link.

### 🔴 Advanced AI Telemetry (AcousticBrainz)

* **Beats Count (Raw):** The actual number of beats detected. Essential for calculating **Beat Density** (Prog/Math Rock detection).
* **BPM (Acoustic):** High-precision tempo detection (useful to compare against Spotify's BPM to detect rhythmic drift).
* **Danceability Probability:** AI confidence on whether a track is danceable. (Low values often indicate odd time signatures like 7/8).
* **Chord Change Rate:** How frequently the harmony changes.
* **Key Strength:** Confidence in the detected key (Low confidence implies Atonal/Jazz).
* **Mood Probabilities:**
    * Happy / Sad
    * Aggressive / Relaxed
    * Party / Acoustic
    * Electronic / Instrumental


* **Genre Classifiers:** AI-predicted genres based on audio signal.
    * `Genre Rosamerica`: (Cla, Dan, Hip, Jaz, Pop, Rhy, Roc, Spe)
    * `Genre Tzanetakis`: (Blu, Cla, Cou, Dis, Hip, Jaz, Met, Pop, Reg, Roc)



### 🛡️ Acknowledgments

* **AcousticBrainz:** For providing the Essentia music analysis data.
* **MusicBrainz:** For the open-source metadata database.
* **Spotify API:** Metadata resolution.
* **ReccoBeats API:** Audio feature telemetry.
* **Power BI:** Recommended for final data visualization and transformation.
