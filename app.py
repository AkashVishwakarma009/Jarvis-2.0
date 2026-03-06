"""
app.py - Flask web server for the Jarvis AI Assistant.

Provides a browser-based frontend that communicates with the
same command engine used by the desktop GUI.

Usage:
    python app.py
    Then open http://localhost:5000 in your browser.
"""

import sys
import os
import datetime
import json

# Ensure the jarvis package is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis"))

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

from config import ASSISTANT_NAME, WAKE_WORD, SCHEDULED_REMINDERS
from commands import handle_command

# ──────────────────────────────────────────────
#  App setup
# ──────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
app.config["SECRET_KEY"] = "jarvis-secret-key-2026"
socketio = SocketIO(app, cors_allowed_origins="*")

# ──────────────────────────────────────────────
#  State tracking
# ──────────────────────────────────────────────
_state = {
    "status": "idle",
    "command_count": 0,
}


def _get_greeting() -> str:
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return f"{greeting}, sir. I am {ASSISTANT_NAME}, your personal AI assistant. How can I help you?"


# ──────────────────────────────────────────────
#  HTTP routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main frontend page."""
    return render_template("index.html", assistant_name=ASSISTANT_NAME)


@app.route("/api/status")
def api_status():
    """Return the current assistant state."""
    return jsonify({
        "status": _state["status"],
        "command_count": _state["command_count"],
        "assistant_name": ASSISTANT_NAME,
        "time": datetime.datetime.now().strftime("%I:%M %p"),
        "date": datetime.datetime.now().strftime("%A, %b %d, %Y"),
    })


@app.route("/api/command", methods=["POST"])
def api_command():
    """Process a text command and return Jarvis's response."""
    data = request.get_json(force=True)
    command = data.get("command", "").strip().lower()

    if not command:
        return jsonify({"error": "No command provided"}), 400

    _state["status"] = "processing"
    _state["command_count"] += 1

    try:
        response = handle_command(command)
    except SystemExit:
        response = "Goodbye, sir! Have a great day!"
    except Exception as exc:
        _state["status"] = "error"
        return jsonify({"error": str(exc)}), 500

    _state["status"] = "idle"

    return jsonify({
        "response": response,
        "command_count": _state["command_count"],
        "status": "idle",
    })


@app.route("/api/greeting")
def api_greeting():
    """Return a time-appropriate greeting."""
    return jsonify({"greeting": _get_greeting()})


@app.route("/assets/<path:filename>")
def serve_asset(filename):
    """Serve avatar and other assets from the jarvis/assets folder."""
    assets_dir = os.path.join(os.path.dirname(__file__), "jarvis", "assets")
    return send_from_directory(assets_dir, filename)


# ──────────────────────────────────────────────
#  WebSocket events (real-time communication)
# ──────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    emit("greeting", {"message": _get_greeting()})
    emit("status", {"status": "idle"})


@socketio.on("command")
def on_command(data):
    command = data.get("command", "").strip().lower()
    if not command:
        emit("error", {"message": "No command provided"})
        return

    emit("status", {"status": "processing"})
    _state["status"] = "processing"
    _state["command_count"] += 1

    try:
        response = handle_command(command)
    except SystemExit:
        response = "Goodbye, sir! Have a great day!"
    except Exception as exc:
        _state["status"] = "error"
        emit("error", {"message": str(exc)})
        emit("status", {"status": "idle"})
        return

    _state["status"] = "idle"
    emit("response", {
        "message": response,
        "command_count": _state["command_count"],
    })
    emit("status", {"status": "idle"})


# ──────────────────────────────────────────────
#  Scheduled reminders (background thread)
# ──────────────────────────────────────────────
import time as _time
import threading as _threading

_fired_reminders: set = set()

def _reminder_loop():
    """Background thread that checks reminders every 30 seconds."""
    global _fired_reminders
    while True:
        now = datetime.datetime.now()
        today_key = now.strftime("%Y-%m-%d")

        for hour, minute, message in SCHEDULED_REMINDERS:
            reminder_id = f"{today_key}-{hour:02d}:{minute:02d}"
            if reminder_id in _fired_reminders:
                continue
            if now.hour == hour and now.minute == minute:
                _fired_reminders.add(reminder_id)
                # Broadcast to all connected browsers
                socketio.emit("reminder", {"message": message})
                print(f"[Reminder] {message}")

        # Reset at midnight
        if now.hour == 0 and now.minute == 0:
            _fired_reminders.clear()

        _time.sleep(30)


# ──────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n  ◆ {ASSISTANT_NAME} Web Interface")
    print(f"  ◆ Open http://localhost:5000 in your browser\n")

    # Start reminder checker in background
    _reminder_thread = _threading.Thread(target=_reminder_loop, daemon=True)
    _reminder_thread.start()

    # Use waitress (production server) — no more "development server" warning
    from waitress import serve
    print("  ◆ Server running with Waitress (production mode)\n")
    serve(app, host="0.0.0.0", port=5000)
