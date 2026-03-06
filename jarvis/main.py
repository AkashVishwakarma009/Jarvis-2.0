"""
main.py - Entry point for the Jarvis AI Assistant.

Runs an infinite loop that:
  1. Passively listens for the wake word ("Hey Jarvis").
  2. Once activated, listens for a command.
  3. Routes the command to the appropriate handler.
  4. Speaks the response and returns to passive listening.

Usage:
    python main.py          # Terminal (voice-only) mode
    python main.py --gui    # Launch the graphical interface
"""

import sys
import os

# Ensure the jarvis package directory is on the path so sibling
# modules can be imported when running main.py directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ASSISTANT_NAME, WAKE_WORD
from speech_engine import speak, listen
from commands import handle_command


# ──────────────────────────────────────────────
#  Greeting
# ──────────────────────────────────────────────

def greet() -> None:
    """Play a startup greeting."""
    import datetime
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    speak(f"{greeting}, sir. I am {ASSISTANT_NAME}, your personal AI assistant. How can I help you?")


# ──────────────────────────────────────────────
#  Wake-word detection (passive listening)
# ──────────────────────────────────────────────

def wait_for_wake_word() -> None:
    """
    Block until the wake word is detected.
    Uses a long phrase limit so the user can speak naturally.
    """
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.pause_threshold = 1.0

    print(f'\nSay "{WAKE_WORD.title()}" to activate ...')

    while True:
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=4)
                text = recognizer.recognize_google(audio).lower()
                if WAKE_WORD in text:
                    print(f"[Wake word detected] {text}")
                    return
            except (sr.UnknownValueError, sr.WaitTimeoutError):
                # Didn't catch anything — keep looping silently
                continue
            except sr.RequestError as exc:
                print(f"[Error] Speech service unavailable: {exc}")
                continue


# ──────────────────────────────────────────────
#  Main loop
# ──────────────────────────────────────────────

def main() -> None:
    greet()

    while True:
        try:
            # Step 1 — Wait for activation
            wait_for_wake_word()

            # Step 2 — Acknowledge & listen for the actual command
            speak("Yes sir, I'm listening.")
            command = listen()

            if not command:
                speak("I didn't hear anything. Please try again.")
                continue

            # Step 3 — Process the command
            response = handle_command(command)

            # Step 4 — Speak the result
            if response:
                speak(response)

        except KeyboardInterrupt:
            speak("Shutting down. Goodbye, sir.")
            break
        except SystemExit:
            break
        except Exception as exc:
            print(f"[Unexpected error] {exc}")
            speak("I encountered an error. Let me try again.")
            continue


if __name__ == "__main__":
    if "--gui" in sys.argv:
        from gui import main as gui_main
        gui_main()
    else:
        main()
