"""
commands.py - Command router for the Jarvis AI Assistant.

Maps recognised voice input to the correct automation function.
Each handler receives the raw command string and returns a spoken
response (or None to stay silent).
"""

from __future__ import annotations

import re
from typing import Callable

from speech_engine import speak, listen
import automation as auto

# ──────────────────────────────────────────────
#  Keyword → handler registry
# ──────────────────────────────────────────────

# Each entry is (list_of_trigger_phrases, handler_function).
# The router picks the FIRST match, so order matters — put
# more specific phrases before generic ones.

_ROUTES: list[tuple[list[str], Callable[[str], str | None]]] = []


def _route(triggers: list[str]):
    """Decorator: register a handler for one or more trigger phrases."""
    def decorator(func: Callable[[str], str | None]):
        _ROUTES.append((triggers, func))
        return func
    return decorator


# ──────────────────────────────────────────────
#  Command handlers (ordered by specificity)
# ──────────────────────────────────────────────

# --- Greetings -----------------------------------------------------------

@_route(["hello", "hi jarvis", "hey", "good morning", "good evening"])
def _greet(cmd: str) -> str:
    return "Hello! How can I help you today?"


# --- Open applications ----------------------------------------------------

@_route(["open chrome", "launch chrome", "start chrome"])
def _open_chrome(cmd: str) -> str:
    auto.open_application("chrome")
    return "Opening Google Chrome."


@_route(["open vs code", "open vscode", "launch vs code", "open visual studio code"])
def _open_vscode(cmd: str) -> str:
    auto.open_application("vscode")
    return "Opening Visual Studio Code."


@_route(["open notepad", "launch notepad", "start notepad"])
def _open_notepad(cmd: str) -> str:
    auto.open_application("notepad")
    return "Opening Notepad."


@_route(["open calculator", "launch calculator", "open calc"])
def _open_calc(cmd: str) -> str:
    auto.open_application("calc")
    return "Opening Calculator."


@_route(["open command prompt", "open cmd", "open terminal"])
def _open_cmd(cmd: str) -> str:
    auto.open_application("cmd")
    return "Opening Command Prompt."


@_route(["open explorer", "open file explorer", "open files"])
def _open_explorer(cmd: str) -> str:
    auto.open_application("explorer")
    return "Opening File Explorer."


# --- Web searches ---------------------------------------------------------

@_route(["search google", "google search", "google for", "search for"])
def _search_google(cmd: str) -> str:
    # Strip the trigger portion to isolate the query
    query = re.sub(
        r"(search google for|google search for|google for|search for|search google|google search)",
        "", cmd,
    ).strip()
    if not query:
        query = listen("What should I search for on Google?")
    if query:
        auto.search_google(query)
        return f"Searching Google for {query}."
    return "I didn't catch the search query."


@_route(["search youtube", "youtube search", "play on youtube", "youtube for"])
def _search_youtube(cmd: str) -> str:
    query = re.sub(
        r"(search youtube for|youtube search for|youtube for|search youtube|youtube search|play on youtube)",
        "", cmd,
    ).strip()
    if not query:
        query = listen("What should I search for on YouTube?")
    if query:
        auto.search_youtube(query)
        return f"Searching YouTube for {query}."
    return "I didn't catch the search query."


# --- Type text ------------------------------------------------------------

@_route(["type", "write"])
def _type_text(cmd: str) -> str:
    text = re.sub(r"^(type|write)\s*", "", cmd).strip()
    if not text:
        text = listen("What would you like me to type?")
    if text:
        auto.type_text_unicode(text)
        return "Done typing."
    return "I didn't catch what to type."


# --- Mouse ----------------------------------------------------------------

@_route(["click", "left click"])
def _click(cmd: str) -> str:
    auto.click_mouse("left")
    return "Clicked."


@_route(["right click"])
def _right_click(cmd: str) -> str:
    auto.click_mouse("right")
    return "Right clicked."


@_route(["double click"])
def _double_click(cmd: str) -> str:
    auto.double_click_mouse()
    return "Double clicked."


@_route(["scroll up"])
def _scroll_up(cmd: str) -> str:
    auto.scroll_mouse(5)
    return "Scrolling up."


@_route(["scroll down"])
def _scroll_down(cmd: str) -> str:
    auto.scroll_mouse(-5)
    return "Scrolling down."


# --- Keyboard shortcuts ---------------------------------------------------

@_route(["press enter", "hit enter"])
def _press_enter(cmd: str) -> str:
    auto.press_key("enter")
    return "Enter pressed."


@_route(["press escape", "hit escape", "press esc"])
def _press_escape(cmd: str) -> str:
    auto.press_key("escape")
    return "Escape pressed."


@_route(["copy", "copy that"])
def _copy(cmd: str) -> str:
    auto.hotkey("ctrl", "c")
    return "Copied to clipboard."


@_route(["paste", "paste that"])
def _paste(cmd: str) -> str:
    auto.hotkey("ctrl", "v")
    return "Pasted."


@_route(["undo"])
def _undo(cmd: str) -> str:
    auto.hotkey("ctrl", "z")
    return "Undo."


@_route(["redo"])
def _redo(cmd: str) -> str:
    auto.hotkey("ctrl", "y")
    return "Redo."


@_route(["select all"])
def _select_all(cmd: str) -> str:
    auto.hotkey("ctrl", "a")
    return "Selected all."


@_route(["save", "save file"])
def _save(cmd: str) -> str:
    auto.hotkey("ctrl", "s")
    return "Saved."


@_route(["close window", "close tab", "close this"])
def _close(cmd: str) -> str:
    auto.hotkey("alt", "F4")
    return "Closing window."


@_route(["minimize", "minimize window"])
def _minimize(cmd: str) -> str:
    auto.hotkey("win", "down")
    return "Minimized."


@_route(["maximize", "maximize window"])
def _maximize(cmd: str) -> str:
    auto.hotkey("win", "up")
    return "Maximized."


@_route(["switch window", "alt tab"])
def _alt_tab(cmd: str) -> str:
    auto.hotkey("alt", "tab")
    return "Switching window."


# --- Screenshot -----------------------------------------------------------

@_route(["take a screenshot", "screenshot", "capture screen", "take screenshot"])
def _screenshot(cmd: str) -> str:
    path = auto.take_screenshot()
    return f"Screenshot saved to {path}."


# --- Volume ---------------------------------------------------------------

@_route(["volume up", "increase volume", "louder"])
def _volume_up(cmd: str) -> str:
    auto.volume_up()
    return "Volume increased."


@_route(["volume down", "decrease volume", "quieter", "lower volume"])
def _volume_down(cmd: str) -> str:
    auto.volume_down()
    return "Volume decreased."


@_route(["mute", "unmute", "toggle mute"])
def _mute(cmd: str) -> str:
    auto.volume_mute()
    return "Toggled mute."


# --- Folders & files ------------------------------------------------------

@_route(["open folder", "open directory"])
def _open_folder(cmd: str) -> str:
    folder = re.sub(r"(open folder|open directory)\s*", "", cmd).strip()
    if not folder:
        folder = listen("Which folder should I open?")
    if folder and auto.open_folder(folder):
        return f"Opening folder {folder}."
    return "I couldn't find that folder."


@_route(["open file"])
def _open_file(cmd: str) -> str:
    filepath = re.sub(r"open file\s*", "", cmd).strip()
    if not filepath:
        filepath = listen("Which file should I open?")
    if filepath and auto.open_file(filepath):
        return f"Opening file {filepath}."
    return "I couldn't find that file."


# --- System power ---------------------------------------------------------

@_route(["shutdown", "shut down", "turn off computer", "power off"])
def _shutdown(cmd: str) -> str:
    speak("Are you sure you want to shut down? Say yes to confirm.")
    confirmation = listen()
    if "yes" in confirmation:
        auto.shutdown_pc()
        return "Shutting down in 5 seconds."
    return "Shutdown cancelled."


@_route(["restart", "reboot", "restart computer"])
def _restart(cmd: str) -> str:
    speak("Are you sure you want to restart? Say yes to confirm.")
    confirmation = listen()
    if "yes" in confirmation:
        auto.restart_pc()
        return "Restarting in 5 seconds."
    return "Restart cancelled."


@_route(["lock computer", "lock pc", "lock screen"])
def _lock(cmd: str) -> str:
    auto.lock_pc()
    return "Locking the computer."


@_route(["sleep", "go to sleep", "sleep mode"])
def _sleep(cmd: str) -> str:
    auto.sleep_pc()
    return "Putting the computer to sleep."


# --- Time & date ----------------------------------------------------------

@_route(["what time is it", "tell me the time", "current time", "time please"])
def _tell_time(cmd: str) -> str:
    import datetime
    now = datetime.datetime.now().strftime("%I:%M %p")
    return f"The current time is {now}."


@_route(["what's the date", "tell me the date", "current date", "today's date", "what is the date"])
def _tell_date(cmd: str) -> str:
    import datetime
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    return f"Today is {today}."


# --- Exit the assistant ---------------------------------------------------

@_route(["exit", "quit", "stop", "goodbye", "bye", "go to sleep jarvis"])
def _exit(cmd: str) -> str | None:
    speak("Goodbye, sir. Have a great day!")
    raise SystemExit(0)


# ──────────────────────────────────────────────
#  Public router function
# ──────────────────────────────────────────────

def handle_command(command: str) -> str:
    """
    Match *command* against registered trigger phrases and run the
    corresponding handler.  Returns the spoken response string.
    """
    for triggers, handler in _ROUTES:
        for phrase in triggers:
            if phrase in command:
                response = handler(command)
                return response if response else ""

    return "I'm sorry, I didn't understand that command. Could you repeat?"
