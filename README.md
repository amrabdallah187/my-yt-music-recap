# YouTube Music Audio Feature Extractor & Analyzer

A complete data pipeline that extracts your YouTube Music listening history, enriches it with Spotify metadata, fetches advanced audio telemetry (BPM, Energy, Key), and prepares it for deep analysis.

## 📋 Project Overview

This toolset transforms your raw Google Takeout data into a rich dataset. It maps your YouTube Music history to Spotify IDs and uses the ReccoBeats API to fetch detailed audio metrics for every track.

**The Pipeline:**
1.  **Deduplicate & Search:** `myrecap.py` cleans your history and finds corresponding Spotify IDs.
2.  **Batch Fetch Telemetry:** `reccobeats_call.py` fetches advanced metrics (Tempo, Valence, Liveness, etc.) using a 40-song batch limit.
3.  **Analyze & Clean:** The output is ready for Power BI, Tableau, or Excel for further filtering and visualization.

## 🛠️ Prerequisites

* **Python 3.13+**
* **Spotify Developer Account:** To obtain a Client ID & Secret.
* **Google Takeout:** Your `watch-history.json` file.

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

### Step 2: Fetch Audio Features

Run the fetcher to get audio metrics from the ReccoBeats API. This script is optimized for the strict 40-song batch limit.

* **Input:** `enriched_history.csv`
* **Output:** `reccobeats_audio_features.csv`

```bash
python reccobeats_call.py

```

### Step 3: Analysis & Visualization

The final CSV files are structured for easy import into Business Intelligence tools.

* **Cleaning:** You can perform further data cleaning (e.g., removing outliers, filtering specific dates, or removing non-music entries) directly within **Power BI (Power Query)**, **Excel**, or **Tableau**.
* **Analysis:** Use the audio metrics to find patterns in your mood, energy levels over time, or your most "danceable" months.

### 📂 File Structure

| File | Description |
| --- | --- |
| `myrecap.py` | Cleans raw YouTube data, handles Spotify ID resolution, and saves the history. |
| `reccobeats_call.py` | Specifically fetches audio features from ReccoBeats in batches of 40. |
| `watch-history.json` | Your raw YouTube Music history from Google Takeout. |
| `enriched_history.csv` | Your history mapped to Spotify IDs. |
| `reccobeats_audio_features.csv` | The final dataset containing all 13+ audio metrics. |

### 📊 Data Points

The final dataset includes the following metrics, which can be used to filter and categorize your music history:

* **Timestamp:** The exact date and time the track was played (recorded from your original YouTube Music history).
* **Artist:** The name of the performing artist or band.
* **Title:** The original track title as recorded in your YouTube Music history.
* **Spotify Name:** The standardized track name found on Spotify (useful for verifying search accuracy).
  
* **Valence (Happiness):** (0.0 - 1.0) Measures the emotional tone of a track. High valence feels positive/happy, while low valence feels negative/sad/angry.
* **Energy:** (0.0 - 1.0) Represents intensity and activity. High-energy tracks feel fast, loud, and noisy (e.g., death metal), while low-energy tracks feel calm.
* **Danceability:** (0.0 - 1.0) How suitable a track is for dancing based on tempo, rhythm stability, beat strength, and overall regularity.
* **Tempo:** The overall estimated tempo of a track in beats per minute (BPM).
* **Key & Mode:** * **Key:** The key the track is in (e.g., 0 = C, 1 = C♯/D♭, etc.).
* **Mode:** The modality (Major = 1, Minor = 0) of the track.
* **Loudness:** The overall loudness of a track in decibels (dB), averaged across the entire track.
* **Acousticness:** (0.0 - 1.0) A confidence measure of whether the track is acoustic (natural sounds) versus synthetic/electronic.
* **Instrumentalness:** (0.0 - 1.0) Predicts whether a track contains no vocals. The closer to 1.0, the greater the likelihood the track is purely instrumental.
* **Liveness:** (0.0 - 1.0) Detects the presence of an audience in the recording. Higher values indicate a higher probability that the track was performed live.
* **Speechiness:** (0.0 - 1.0) Detects the presence of spoken words. Values above 0.66 describe tracks like talk shows or audiobooks; values below 0.33 represent music.
  
* **ID & Metadata:**
  * **ID:** Unique identifier for the track (Spotify/ReccoBeats ID).
  * **ISRC:** International Standard Recording Code.
  * **Href:** Direct link to the track on Spotify.

### 🛡️ Acknowledgments

* **Spotify API:** Metadata resolution.
* **ReccoBeats API:** Audio feature telemetry.
* **Power BI:** Recommended for final data visualization and transformation.
