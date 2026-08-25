#!/usr/bin/env python3
"""Local dev server for the vOICe simulator.

Serves this repo (web/, stimuli/) exactly like `python3 -m http.server`,
plus one extra endpoint the browser uses to save a finished run straight
to disk:

    POST /api/save-run   body: {"filename": "...", "csv": "..."}
    -> writes test_data/<sanitized filename>, or IR_VOICE_TEST_DATA_DIR when set
    -> also mirrors the same bytes to IR_VOICE_TEST_DATA_MIRROR_DIR when set

test_data/ is gitignored, so results never end up in the (public) repo.
Binds to localhost only -- not reachable from the rest of the LAN.
"""
import http.server
import json
import os
import re
import socketserver
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.environ.get(
    "IR_VOICE_TEST_DATA_DIR",
    os.path.join(ROOT, "test_data"),
)
MIRROR_TEST_DATA_DIR = os.environ.get("IR_VOICE_TEST_DATA_MIRROR_DIR")
TEST_DATA_DIRS = tuple(dict.fromkeys(
    os.path.realpath(path)
    for path in (TEST_DATA_DIR, MIRROR_TEST_DATA_DIR)
    if path
))
SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")
MAX_BODY_BYTES = 20_000_000  # 20MB sanity cap; a run's CSV is a few KB.


# The page is edited often during development, and a stale cached copy of
# index.html/app.js silently running old logic (missing metrics, missing
# buttons) is worse than a slower load -- so never let the browser cache
# these two. Stimuli (wav/png) don't change once generated, so those keep
# normal caching for load performance.
NO_CACHE_PATHS = ("/web/index.html", "/web/app.js", "/", "")


def save_result_copies(safe_name, csv_text):
    """Write identical result bytes to every configured result directory."""
    destinations = []
    for directory in TEST_DATA_DIRS:
        os.makedirs(directory, exist_ok=True)
        destination = os.path.join(directory, safe_name)
        with open(destination, "w", newline="") as output:
            output.write(csv_text)
        destinations.append(destination)
    return destinations


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        path = self.path.split("?")[0]
        if path in NO_CACHE_PATHS or path.endswith((".html", ".js", ".mjs")):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self):
        if self.path != "/api/save-run":
            self.send_error(404, "Unknown endpoint")
            return

        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_BODY_BYTES:
            self.send_error(400, "Bad content length")
            return
        body = self.rfile.read(length)

        try:
            payload = json.loads(body)
            filename = payload["filename"]
            csv_text = payload["csv"]
        except (KeyError, json.JSONDecodeError):
            self.send_error(400, "Expected JSON {filename, csv}")
            return

        # Never trust the client's filename for path components.
        safe_name = SAFE_NAME.sub("_", os.path.basename(filename)) or "run"
        if not safe_name.endswith(".csv"):
            safe_name += ".csv"

        try:
            destinations = save_result_copies(safe_name, csv_text)
        except OSError as error:
            self.send_error(500, f"Could not save every CSV copy: {error}")
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "saved": True,
            "path": destinations[0],
            "paths": destinations,
        }).encode())


class LocalTCPServer(socketserver.TCPServer):
    # A packaged app may be closed and reopened immediately. macOS can retain
    # the previous listener in TIME_WAIT briefly, so permit the same local port
    # to be rebound without making the launcher appear broken.
    allow_reuse_address = True


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    for result_directory in TEST_DATA_DIRS:
        os.makedirs(result_directory, exist_ok=True)
    with LocalTCPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"Serving {ROOT} at http://localhost:{port}")
        print(f"POST /api/save-run writes into {', '.join(TEST_DATA_DIRS)}")
        httpd.serve_forever()
