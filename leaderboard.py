"""Read-only LAN API for the Cyber Defender leaderboard."""

import json
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


PORT = 8765
DIFFICULTIES = ("Easy", "Normal", "Hard", "Extreme")


def get_local_ip():
    """Return the LAN address selected for outbound network traffic."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 9))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


def _read_scores(file_path):
    scores = {difficulty: [] for difficulty in DIFFICULTIES}
    if not os.path.exists(file_path):
        return scores

    with open(file_path, "r", encoding="utf-8") as file:
        saved = json.load(file)

    if not isinstance(saved, dict):
        raise ValueError("Leaderboard data must be a JSON object")

    for difficulty in DIFFICULTIES:
        entries = saved.get(difficulty, [])
        if not isinstance(entries, list):
            continue

        valid_entries = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            waves = entry.get("waves")
            if isinstance(name, str) and type(waves) is int and waves >= 0:
                valid_entries.append({"name": name, "waves": waves})

        scores[difficulty] = sorted(
            valid_entries,
            key=lambda entry: entry["waves"],
            reverse=True
        )[:10]

    return scores


def create_server(file_path, host="0.0.0.0", port=PORT):
    """Create the read-only HTTP server without starting its thread."""
    absolute_file_path = os.path.abspath(file_path)

    class LeaderboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = urlsplit(self.path).path
            if route == "/health":
                self._send_json(200, {"status": "ok"})
                return

            if route != "/api/leaderboard":
                self._send_json(404, {"error": "Not found"})
                return

            try:
                scores = _read_scores(absolute_file_path)
            except (OSError, json.JSONDecodeError, ValueError):
                self._send_json(503, {"error": "Leaderboard is unavailable"})
                return

            self._send_json(200, {"scores": scores})

        def _send_json(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format_string, *args):
            return

    class ReusableThreadingHTTPServer(ThreadingHTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    return ReusableThreadingHTTPServer((host, port), LeaderboardHandler)


def start_server(file_path, host="0.0.0.0", port=PORT):
    """Start the read-only leaderboard service on a daemon thread."""
    server = create_server(file_path, host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
