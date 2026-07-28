import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

from mutagen import File as MutagenFile

from .models import LocalTrack

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wma", ".wav", ".aiff"}


class LocalScanner:
    """Recursively scan a folder for music files and extract metadata."""

    @staticmethod
    def _get_duration_ms(filepath: str) -> int:
        try:
            audio = MutagenFile(filepath)
            if audio is not None and audio.info is not None:
                return int(audio.info.length * 1000)
        except Exception:
            pass
        return 0

    @staticmethod
    def _extract_tags(filepath: str) -> Optional[Dict[str, str]]:
        try:
            audio = MutagenFile(filepath, easy=True)
            if audio is None:
                return None
            tags: Dict[str, str] = {}
            for key in ("artist", "title", "album", "tracknumber", "date"):
                val = audio.get(key, [""])[0]
                tags[key] = val.strip() if val else ""
            return tags
        except Exception:
            return None

    @staticmethod
    def _parse_filename(filepath: str) -> Dict[str, str]:
        """Fallback: guess artist/title/album from path and filename."""
        name = Path(filepath).stem
        parts = Path(filepath).parts

        result: Dict[str, str] = {"artist": "", "title": "", "album": ""}

        # Try "Artist - Title" pattern
        if " - " in name:
            split = name.split(" - ", 1)
            result["artist"] = split[0].strip()
            result["title"] = split[1].strip()
        elif ". " in name:
            split = name.split(". ", 1)
            if len(split) == 2 and split[0].strip().isdigit():
                result["title"] = split[1].strip()
            else:
                result["title"] = name
        else:
            result["title"] = name

        # Infer artist/album from parent folders
        if len(parts) >= 3:
            result["artist"] = result["artist"] or parts[-3]
            result["album"] = parts[-2]
        elif len(parts) >= 2:
            result["album"] = result["album"] or parts[-2]

        return result

    @classmethod
    def scan(
        cls,
        folder: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[LocalTrack]:
        folder = str(folder)
        tracks: List[LocalTrack] = []
        music_files: List[str] = []

        for root, _dirs, files in os.walk(folder):
            for f in files:
                ext = Path(f).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    music_files.append(os.path.join(root, f))

        total = len(music_files)

        for i, filepath in enumerate(music_files):
            if progress_callback:
                # Show short filename instead of full path
                short = os.path.basename(filepath)
                progress_callback(i + 1, total, short)

            try:
                fmt = Path(filepath).suffix.lower().lstrip(".")
                file_size = os.path.getsize(filepath)
                duration = cls._get_duration_ms(filepath)

                tags = cls._extract_tags(filepath)

                if tags and (tags.get("artist") or tags.get("title")):
                    tn_raw = tags.get("tracknumber", "0")
                    try:
                        track_num = int(tn_raw.split("/")[0])
                    except (ValueError, IndexError):
                        track_num = 0

                    track = LocalTrack(
                        filepath=filepath,
                        artist=tags.get("artist", "") or "",
                        title=tags.get("title", "") or "",
                        album=tags.get("album", "") or "",
                        track_number=track_num,
                        duration_ms=duration,
                        file_format=fmt,
                        file_size=file_size,
                    )
                else:
                    parsed = cls._parse_filename(filepath)
                    track = LocalTrack(
                        filepath=filepath,
                        artist=parsed["artist"],
                        title=parsed["title"],
                        album=parsed["album"],
                        track_number=0,
                        duration_ms=duration,
                        file_format=fmt,
                        file_size=file_size,
                    )

                tracks.append(track)

            except Exception:
                continue  # skip problematic files silently

        if progress_callback:
            progress_callback(total, total, "Done — {} tracks found".format(total))

        return tracks
