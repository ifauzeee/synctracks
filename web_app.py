"""SyncTracks — Flask web app to match CSV tracks against local music files."""

import os
import uuid
import json
import threading
import time
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify, Response,
    stream_with_context, redirect, url_for,
)

import sys
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from src.models import TrackRecord, LocalTrack
from src.importer import import_file, import_local_file
from src.matcher import Matcher

# ── app factory ──────────────────────────────────────────────────────────

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB

UPLOAD_DIR = _HERE / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {'.csv', '.json'}

# In-memory session store
# { session_id: { status, progress, phase, result, error } }
sessions: dict = {}


# ── helpers ──────────────────────────────────────────────────────────────

def _allowed_file(name: str) -> bool:
    return '.' in name and Path(name).suffix.lower() in ALLOWED_EXT


def _result_to_dict(result, source_tracks, local_tracks):
    """Serialize MatchResult + metadata to a plain dict for templates."""
    matched_rows = []
    for tr, lt in result.matched:
        matched_rows.append({
            "source_artist": tr.artist,
            "source_title": tr.title,
            "source_album": tr.album,
            "local_artist": lt.artist,
            "local_title": lt.title,
            "local_album": lt.album,
            "local_filepath": lt.filepath,
            "source_duration": tr.duration_ms,
            "local_duration": lt.duration_ms,
        })

    unmatched_source = [
        {
            "artist": tr.artist, "title": tr.title,
            "album": tr.album, "duration_ms": tr.duration_ms,
        }
        for tr in result.unmatched_source
    ]

    unmatched_local = [
        {
            "artist": lt.artist, "title": lt.title,
            "album": lt.album, "filepath": lt.filepath,
            "duration_ms": lt.duration_ms,
        }
        for lt in result.unmatched_local
    ]

    return {
        "matched": matched_rows,
        "unmatched_source": unmatched_source,
        "unmatched_local": unmatched_local,
        "total_source": result.total_source,
        "total_local": result.total_local,
        "matched_count": len(result.matched),
        "unmatched_source_count": len(result.unmatched_source),
        "unmatched_local_count": len(result.unmatched_local),
        "match_percentage": result.match_percentage,
    }


def _run_matching(sid: str, source_path: str, local_path: str):
    """Background thread: import → match → store result."""
    try:
        sessions[sid] = {
            "status": "importing", "progress": 0,
            "phase": "Importing source tracks…",
        }

        source_tracks = import_file(source_path)
        sessions[sid].update({
            "progress": 15,
            "phase": f"Found {len(source_tracks)} source tracks. Importing local tracks…",
        })

        local_tracks = import_local_file(local_path)
        sessions[sid].update({
            "progress": 30,
            "phase": f"Imported {len(local_tracks)} local tracks. Matching…",
        })

        matcher = Matcher()
        total = len(source_tracks)

        def progress_cb(step: int, total_steps: int):
            pct = 30 + int((step / max(total_steps, 1)) * 65)
            sessions[sid].update({
                "status": "matching",
                "progress": min(pct, 95),
                "phase": f"Matching {step}/{total_steps}…",
            })

        result = matcher.match(
            source_tracks, local_tracks,
            progress_callback=progress_cb,
        )

        sessions[sid] = {
            "status": "complete",
            "progress": 100,
            "phase": "Done!",
            "result": _result_to_dict(result, source_tracks, local_tracks),
        }
    except Exception as exc:
        import traceback
        sessions[sid] = {
            "status": "error",
            "progress": 0,
            "phase": str(exc),
            "error": traceback.format_exc(),
        }
    finally:
        # Cleanup uploaded files
        try:
            os.remove(source_path)
            os.remove(local_path)
        except OSError:
            pass


# ── routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Accept source + local CSV/JSON files and start matching in background."""
    source_file = request.files.get("source")
    local_file = request.files.get("local")

    if not source_file or not local_file:
        return jsonify({"error": "Both source and local files are required"}), 400

    if not _allowed_file(source_file.filename):
        return jsonify({"error": f"Unsupported source file: {source_file.filename}"}), 400
    if not _allowed_file(local_file.filename):
        return jsonify({"error": f"Unsupported local file: {local_file.filename}"}), 400

    sid = uuid.uuid4().hex[:12]

    src_ext = Path(source_file.filename).suffix.lower()
    local_ext = Path(local_file.filename).suffix.lower()

    src_path = UPLOAD_DIR / f"{sid}_source{src_ext}"
    local_path = UPLOAD_DIR / f"{sid}_local{local_ext}"

    source_file.save(str(src_path))
    local_file.save(str(local_path))

    sessions[sid] = {"status": "queued", "progress": 0, "phase": "Starting…"}

    thread = threading.Thread(
        target=_run_matching, args=(sid, str(src_path), str(local_path)),
        daemon=True,
    )
    thread.start()

    return jsonify({"session_id": sid})


@app.route("/progress/<sid>")
def progress(sid):
    """SSE endpoint: stream matching progress to the browser."""
    def generate():
        last_status = ""
        while True:
            data = sessions.get(sid, {"status": "not_found", "phase": "Session not found"})
            current_status = data.get("status", "")

            yield f"data: {json.dumps(data)}\n\n"

            if current_status in ("complete", "error", "not_found"):
                break

            # Only sleep when status hasn't changed to reduce latency
            if current_status == last_status:
                time.sleep(0.3)
            last_status = current_status

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/results/<sid>")
def results(sid):
    """Render results page (matched / unmatched tables)."""
    data = sessions.get(sid)
    if not data:
        return render_template("results.html", error="Session not found.")

    if data.get("status") == "error":
        return render_template("results.html", error=data.get("phase"), traceback=data.get("error"))

    if data.get("status") != "complete":
        return redirect(url_for("index"))

    result = data.get("result", {})
    return render_template("results.html", result=result)


@app.route("/session/<sid>/status")
def session_status(sid):
    """JSON endpoint for polling session status."""
    data = sessions.get(sid)
    if not data:
        return jsonify({"status": "not_found"})
    # Don't send full result in poll — only in SSE
    return jsonify({
        "status": data.get("status"),
        "progress": data.get("progress"),
        "phase": data.get("phase"),
    })


# ── entry ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SyncTracks Web")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8080, help="Port")
    args = parser.parse_args()
    print(f"SyncTracks running on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True, threaded=True)
