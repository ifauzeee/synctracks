"""
Scan music files on Android and export as CSV for SyncTracks.

Usage in Termux:
  1. termux-setup-storage
  2. pkg install python
  3. pip install mutagen
  4. python scan.py ~/storage/music
  5. Output: music_tracks.csv
"""

import csv
import sys
from pathlib import Path

AUDIO_EXTENSIONS = {
    '.mp3', '.flac', '.m4a', '.aac', '.ogg',
    '.wav', '.wma', '.opus', '.alac', '.aiff',
    '.ape', '.wv', '.tta',
}


def read_tag(audio, keys):
    for k in keys:
        try:
            val = str(audio[k][0])
            if val.strip():
                return val.strip()
        except (KeyError, IndexError, TypeError):
            pass
    return ''


def extract_metadata(filepath):
    ext = filepath.suffix.lower()
    title = artist = album = ''
    try:
        if ext == '.mp3':
            from mutagen.mp3 import MP3
            audio = MP3(filepath)
            title = read_tag(audio, ['TIT2'])
            artist = read_tag(audio, ['TPE1'])
            album = read_tag(audio, ['TALB'])
        elif ext == '.flac':
            from mutagen.flac import FLAC
            audio = FLAC(filepath)
            title = read_tag(audio, ['title'])
            artist = read_tag(audio, ['artist'])
            album = read_tag(audio, ['album'])
        elif ext in ('.m4a', '.alac'):
            from mutagen.mp4 import MP4
            audio = MP4(filepath)
            title = read_tag(audio, ['\xa9nam'])
            artist = read_tag(audio, ['\xa9ART'])
            album = read_tag(audio, ['\xa9alb'])
        elif ext in ('.ogg', '.opus'):
            import mutagen
            audio = mutagen.File(filepath)
            if audio:
                title = read_tag(audio, ['title'])
                artist = read_tag(audio, ['artist'])
                album = read_tag(audio, ['album'])
        elif ext == '.aiff':
            from mutagen.aiff import AIFF
            audio = AIFF(filepath)
            title = read_tag(audio, ['TIT2'])
            artist = read_tag(audio, ['TPE1'])
            album = read_tag(audio, ['TALB'])
        elif ext in ('.wma', '.asf'):
            from mutagen.asf import ASF
            audio = ASF(filepath)
            title = read_tag(audio, ['Title'])
            artist = read_tag(audio, ['Author'])
            album = read_tag(audio, ['WM/AlbumTitle'])
    except ImportError as e:
        print(f"  SKIP {filepath.name}: library {e.name} not available")
    except Exception:
        pass
    return title, artist, album


def scan_folder(folder_path):
    tracks = []
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists():
        print(f"ERROR: Folder not found: {folder}")
        print("Run: termux-setup-storage")
        print("Or try: /sdcard/Music")
        sys.exit(1)
    print(f"Scan folder: {folder}")
    audio_files = [f for f in folder.rglob('*')
                   if f.suffix.lower() in AUDIO_EXTENSIONS and f.is_file()]
    total = len(audio_files)
    if not total:
        print(f"No music files found in {folder}")
        sys.exit(1)
    print(f"Found {total} music files. Processing...")
    for i, fp in enumerate(audio_files, 1):
        try:
            title, artist, album = extract_metadata(fp)
            if not artist and ' - ' in fp.stem:
                parts = fp.stem.split(' - ', 1)
                artist = parts[0].strip()
                title = parts[1].strip()
            tracks.append({
                'title': title or fp.stem,
                'artist': artist or 'Unknown Artist',
                'album': album or 'Unknown Album',
            })
            if i % 200 == 0 or i == total:
                print(f"  {i}/{total} - {fp.parent.name}/{fp.name}")
        except Exception:
            tracks.append({
                'title': fp.stem,
                'artist': 'Unknown Artist',
                'album': 'Unknown Album',
            })
    return tracks


def main():
    if len(sys.argv) < 2:
        print("Usage: python scan.py <folder>")
        print("Example: python scan.py ~/storage/music")
        sys.exit(1)
    try:
        import mutagen
    except ImportError:
        print("ERROR: mutagen is not installed. Run: pip install mutagen")
        sys.exit(1)
    folder = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else 'music_tracks.csv'
    tracks = scan_folder(folder)
    with open(output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'artist', 'album'])
        writer.writeheader()
        writer.writerows(tracks)
    print(f"\nDone! {len(tracks)} tracks -> {output}")
    print(f"   Transfer {output} to your PC and upload it in SyncTracks.")


if __name__ == '__main__':
    main()
