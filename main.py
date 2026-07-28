"""
SyncTracks — Web app to match CSV source tracks against local music files.
Run this, then open http://localhost:8080 in your browser.
"""

from web_app import app

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SyncTracks — Music Matcher Web")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--debug", action="store_true", default=True, help="Debug mode")
    args = parser.parse_args()

    print(f"SyncTracks running on http://{args.host}:{args.port}")
    print(f"Upload source and local CSV/JSON files to match tracks.")
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
