# SyncTracks

Web app to match CSV/JSON track lists against your local music collection.  
Upload source tracks (Spotify, Apple Music, etc.) + your local music CSV, and get instant matching — no API required.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.1-green)
![License](https://img.shields.io/badge/license-MIT-white)

## Features

- **Import CSV/JSON** — Works with Exportify, TuneMyMusic, Soundiiz exports; columns auto-detected
- **Import local CSV** — Use the Android scanner or export your local library
- **4-level matching** — Exact → base title → fuzzy + duration → cover version fallback
- **Real-time progress** — SSE live progress bar during matching
- **Tabbed results** — Matched / Unmatched Source / Unmatched Local, paginated tables
- **AMOLED black theme** — Pure dark UI, no cards, premium look
- **Mobile accessible** — Open from any device on your network

## Matching Levels

| Level | Method | Example |
|-------|--------|---------|
| 1 | Exact (normalized) | "The Beatles - Hey Jude" = "the beatles - hey jude" |
| 2 | Base title | "Hey Jude (Remastered)" matches "Hey Jude" |
| 3 | Fuzzy artist + title + duration | Catches typos, different versions |
| 4 | Title-only (cover versions) | "Boulevard of Broken Dreams" by a different artist still matches |

## Quick Start

```bash
git clone https://github.com/ifauzeee/synctracks.git
cd synctracks
pip install -r requirements.txt
python main.py
```

Open **http://localhost:8080** in your browser.

> Access from other devices on your network: find your PC's IP (`ipconfig`), then open `http://<YOUR_IP>:8080`.

## Usage

1. Export your playlist from Spotify (via [Exportify](https://exportify.app/)) or other service → save as CSV/JSON
2. Scan your local music folder (see Android/PC guides below) → save as CSV
3. Open **http://localhost:8080**, upload both files, click **Start Matching**

## Scanning Music on Android (Termux)

Use `scan.py` on your phone to build a CSV of your Android music collection.

```bash
pkg install python
pip install mutagen
termux-setup-storage
python scan.py ~/storage/music ~/storage/downloads/music_tracks.csv
```

Transfer `music_tracks.csv` from the Downloads folder to your PC.

**Supported formats:** `.mp3`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.wav`, `.wma`, `.opus`, `.alac`, `.aiff`, `.ape`, `.wv`, `.tta`

## Scanning Music on PC

```bash
python scan.py D:\Musik
# Creates music_tracks.csv in current directory

python scan.py D:\Musik D:\output\my_music.csv
# Custom output path
```

## Project Structure

```
├── main.py              # Flask entry point
├── web_app.py           # Flask app (routes, upload, SSE, matching)
├── scan.py              # Music file scanner (Android/PC)
├── requirements.txt
├── templates/
│   ├── base.html        # Base layout
│   ├── index.html       # Upload page
│   └── results.html     # Results page (tabs, tables, pagination)
├── static/
│   └── style.css        # AMOLED black theme
└── src/
    ├── models.py        # TrackRecord, LocalTrack, MatchResult
    ├── normalizer.py    # Title/artist normalization
    ├── matcher.py       # 4-level matching engine
    ├── importer.py      # CSV/JSON → track objects
    └── theme.py         # Design tokens
```

## Requirements

- Python 3.12+
- [Flask](https://flask.palletsprojects.com/) 3.x
- [Mutagen](https://mutagen.readthedocs.io) — audio metadata reader
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) — fuzzy string matching
- [Unidecode](https://pypi.org/project/Unidecode/) — unicode normalization

## License

MIT
