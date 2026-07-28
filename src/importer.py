"""Import source/local track data from CSV/JSON exports."""

import csv
import json
import re
import uuid
from pathlib import Path
from typing import List, Optional

from .models import LocalTrack, TrackRecord


# ── column name aliases (case-insensitive) ──────────────────────────────

_ARTIST_KEYS = {"artist", "artists", "artist name", "artist name(s)", "artiest", "artists name"}
_TITLE_KEYS = {"title", "name", "track", "song", "track name", "track title", "label"}
_ALBUM_KEYS = {"album", "album name", "album title", "release", "album name"}
_DURATION_KEYS = {"duration", "length", "duration_ms", "duration (ms)", "track duration (ms)", "duration (s)", "ms", "seconds"}
_ADDED_KEYS = {"added_at", "date added", "added at", "added", "date"}
_URL_KEYS = {"url", "spotify_url", "link", "spotify link", "track url", "track preview url", "preview url"}
_ID_KEYS = {"id", "track_id", "spotify_id", "uri", "track uri"}


def _pick_col(headers: List[str], candidates: set) -> Optional[int]:
    """Return index of first header matching one of *candidates* (case-insensitive)."""
    lower = [h.strip().lower() for h in headers]
    for hdr in lower:
        if hdr in candidates:
            return lower.index(hdr)
    return None


def _parse_s(value: str) -> str:
    return (value or "").strip()


def _parse_int(value: str) -> int:
    """Parse duration to milliseconds."""
    v = (value or "").strip()
    if not v:
        return 0
    # mm:ss or h:mm:ss
    m = re.match(r"(\d+):(\d{2})(?::(\d{2}))?$", v)
    if m:
        parts = [int(x) for x in m.groups() if x is not None]
        if len(parts) == 2:
            return (parts[0] * 60 + parts[1]) * 1000
        return (parts[0] * 3600 + parts[1] * 60 + parts[2]) * 1000
    # plain number — assume milliseconds unless small (< 600 = seconds)
    try:
        n = int(v)
        if n < 600:
            n *= 1000
        return n
    except ValueError:
        return 0


def _make_track(artist: str, title: str, album: str,
                duration_ms: int, added_at: str,
                source_url: str, track_id: str) -> TrackRecord:
    return TrackRecord(
        track_id=track_id or f"imported_{uuid.uuid4().hex[:12]}",
        artist=artist or "Unknown Artist",
        title=title or "Unknown Title",
        album=album or "",
        duration_ms=duration_ms or 0,
        added_at=added_at or "",
        source_url=source_url or "",
    )


# ── public API ──────────────────────────────────────────────────────────

def import_csv(path: str) -> List[TrackRecord]:
    """Parse a CSV file into TrackRecord objects. Auto-detects column layout."""
    tracks: List[TrackRecord] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")

        headers = list(reader.fieldnames)
        col_map = {
            "artist": _pick_col(headers, _ARTIST_KEYS),
            "title": _pick_col(headers, _TITLE_KEYS),
            "album": _pick_col(headers, _ALBUM_KEYS),
            "duration": _pick_col(headers, _DURATION_KEYS),
            "added_at": _pick_col(headers, _ADDED_KEYS),
            "url": _pick_col(headers, _URL_KEYS),
            "id": _pick_col(headers, _ID_KEYS),
        }
        # Build lookup: header name -> column index
        lookup = {h: h for h in headers}
        col_names = {role: headers[idx] for role, idx in col_map.items() if idx is not None}

        for row in reader:
            mapped = {role: row.get(hdr, "") for role, hdr in col_names.items()}
            if mapped["artist"] and mapped["title"]:
                dur_raw = mapped.get("duration", "0")
                dur = _parse_int(dur_raw) if isinstance(dur_raw, str) else int(dur_raw or 0)
                t = _make_track(
                    artist=_parse_s(mapped["artist"]),
                    title=_parse_s(mapped["title"]),
                    album=_parse_s(mapped.get("album", "")),
                    duration_ms=dur,
                    added_at=_parse_s(mapped.get("added_at", "")),
                    source_url=_parse_s(mapped.get("url", "")),
                    track_id=_parse_s(mapped.get("id", "")),
                )
                tracks.append(t)
    return tracks


def _json_field(col_map: dict, keys: list, entry: dict, role: str) -> str:
    """Extract a field from a JSON entry by mapped column index."""
    idx = col_map.get(role)
    if idx is None:
        return ""
    val = entry.get(keys[idx], "")
    return str(val) if val is not None else ""


def import_json(path: str) -> List[TrackRecord]:
    """Parse a JSON file (array of objects) into TrackRecord objects."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("JSON must be an array of track objects.")

    if not raw:
        return []

    first = raw[0] if isinstance(raw[0], dict) else {}
    keys = list(first.keys())
    col_map: dict = {
        "artist": _pick_col(keys, _ARTIST_KEYS),
        "title": _pick_col(keys, _TITLE_KEYS),
        "album": _pick_col(keys, _ALBUM_KEYS),
        "duration": _pick_col(keys, _DURATION_KEYS),
        "added_at": _pick_col(keys, _ADDED_KEYS),
        "url": _pick_col(keys, _URL_KEYS),
        "id": _pick_col(keys, _ID_KEYS),
    }

    def _get(entry: dict, role: str) -> str:
        return _json_field(col_map, keys, entry, role)

    tracks: List[TrackRecord] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue

        artist = _parse_s(_get(entry, "artist"))
        title = _parse_s(_get(entry, "title"))
        if not artist or not title:
            continue

        dur_raw = _get(entry, "duration")
        dur = _parse_int(dur_raw) if dur_raw else 0
        tracks.append(_make_track(
            artist=artist,
            title=title,
            album=_parse_s(_get(entry, "album")),
            duration_ms=dur,
            added_at=_parse_s(_get(entry, "added_at")),
            source_url=_parse_s(_get(entry, "url")),
            track_id=_parse_s(_get(entry, "id")),
        ))
    return tracks


def import_file(path: str) -> List[TrackRecord]:
    """Auto-detect format by extension and import source tracks."""
    p = Path(path)
    if p.suffix.lower() == ".csv":
        return import_csv(str(p))
    elif p.suffix.lower() == ".json":
        return import_json(str(p))
    else:
        raise ValueError(f"Unsupported format: {p.suffix}. Use .csv or .json")


# ── local track import (for CSV-vs-CSV matching) ────────────────────────

_LOCAL_FORMAT_KEYS = {"format", "file_format", "type", "extension", "ext"}
_LOCAL_SIZE_KEYS = {"file_size", "size", "filesize", "bytes", "file size"}
_LOCAL_PATH_KEYS = {"filepath", "path", "file", "location", "filename", "file path", "file name"}
_LOCAL_TRACKNUM_KEYS = {"track_number", "track", "track#", "track no", "number", "no", "#"}


def _make_local_track(artist: str, title: str, album: str,
                      duration_ms: int, filepath: str,
                      track_number: int, file_format: str,
                      file_size: int) -> LocalTrack:
    return LocalTrack(
        filepath=filepath or f"{artist or 'Unknown'} - {title or 'Unknown'}",
        artist=artist or "Unknown Artist",
        title=title or "Unknown Title",
        album=album or "",
        track_number=track_number or 0,
        duration_ms=duration_ms or 0,
        file_format=file_format or "",
        file_size=file_size or 0,
    )


def import_local_csv(path: str) -> List[LocalTrack]:
    """Parse a CSV file into LocalTrack objects. Auto-detects column layout."""
    tracks: List[LocalTrack] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")

        headers = list(reader.fieldnames)
        col_map = {
            "artist": _pick_col(headers, _ARTIST_KEYS),
            "title": _pick_col(headers, _TITLE_KEYS),
            "album": _pick_col(headers, _ALBUM_KEYS),
            "duration": _pick_col(headers, _DURATION_KEYS),
            "filepath": _pick_col(headers, _LOCAL_PATH_KEYS),
            "track_number": _pick_col(headers, _LOCAL_TRACKNUM_KEYS),
            "file_format": _pick_col(headers, _LOCAL_FORMAT_KEYS),
            "file_size": _pick_col(headers, _LOCAL_SIZE_KEYS),
        }
        col_names = {role: headers[idx] for role, idx in col_map.items() if idx is not None}

        for row in reader:
            mapped = {role: row.get(hdr, "") for role, hdr in col_names.items()}
            if not mapped.get("artist") and not mapped.get("title"):
                continue
            dur_raw = mapped.get("duration", "0")
            dur = _parse_int(dur_raw) if isinstance(dur_raw, str) else int(dur_raw or 0)
            tn_raw = _parse_s(mapped.get("track_number", "0"))
            tn = int(tn_raw) if tn_raw.isdigit() else 0
            fs_raw = _parse_s(mapped.get("file_size", "0"))
            fs = int(fs_raw) if fs_raw.isdigit() else 0
            t = _make_local_track(
                artist=_parse_s(mapped.get("artist", "")),
                title=_parse_s(mapped.get("title", "")),
                album=_parse_s(mapped.get("album", "")),
                duration_ms=dur,
                filepath=_parse_s(mapped.get("filepath", "")),
                track_number=tn,
                file_format=_parse_s(mapped.get("file_format", "")),
                file_size=fs,
            )
            tracks.append(t)
    return tracks


def import_local_json(path: str) -> List[LocalTrack]:
    """Parse a JSON file (array of objects) into LocalTrack objects."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("JSON must be an array of track objects.")

    if not raw:
        return []

    first = raw[0] if isinstance(raw[0], dict) else {}
    keys = list(first.keys())
    col_map = {
        "artist": _pick_col(keys, _ARTIST_KEYS),
        "title": _pick_col(keys, _TITLE_KEYS),
        "album": _pick_col(keys, _ALBUM_KEYS),
        "duration": _pick_col(keys, _DURATION_KEYS),
        "filepath": _pick_col(keys, _LOCAL_PATH_KEYS),
        "track_number": _pick_col(keys, _LOCAL_TRACKNUM_KEYS),
        "file_format": _pick_col(keys, _LOCAL_FORMAT_KEYS),
        "file_size": _pick_col(keys, _LOCAL_SIZE_KEYS),
    }

    def _get(entry: dict, role: str) -> str:
        return _json_field(col_map, keys, entry, role)

    tracks: List[LocalTrack] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue

        if not _get(entry, "artist") and not _get(entry, "title"):
            continue

        dur_raw = _get(entry, "duration")
        dur = _parse_int(dur_raw) if dur_raw else 0
        tn_raw = _parse_s(_get(entry, "track_number")) or "0"
        tn = int(tn_raw) if tn_raw.isdigit() else 0
        fs_raw = _parse_s(_get(entry, "file_size")) or "0"
        fs = int(fs_raw) if fs_raw.isdigit() else 0
        tracks.append(_make_local_track(
            artist=_parse_s(_get(entry, "artist")),
            title=_parse_s(_get(entry, "title")),
            album=_parse_s(_get(entry, "album")),
            duration_ms=dur,
            filepath=_parse_s(_get(entry, "filepath")),
            track_number=tn,
            file_format=_parse_s(_get(entry, "file_format")),
            file_size=fs,
        ))
    return tracks


def import_local_file(path: str) -> List[LocalTrack]:
    """Auto-detect format by extension and import local tracks."""
    p = Path(path)
    if p.suffix.lower() == ".csv":
        return import_local_csv(str(p))
    elif p.suffix.lower() == ".json":
        return import_local_json(str(p))
    else:
        raise ValueError(f"Unsupported format: {p.suffix}. Use .csv or .json")
