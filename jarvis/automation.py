"""
automation.py - Low-level PC automation helpers for the Jarvis AI Assistant.

Every public function here performs one concrete system action
(open an app, take a screenshot, change volume, etc.).
Higher-level "commands" module decides *when* to call these.
"""

import os
import subprocess
import datetime
import webbrowser

import pyautogui

from config import (
    APP_PATHS,
    SCREENSHOT_DIR,
    GOOGLE_SEARCH_URL,
    YOUTUBE_SEARCH_URL,
    VOLUME_STEP,
)

# Safety: pyautogui will raise an exception if the cursor hits a corner
pyautogui.FAILSAFE = True
# Slight pause between pyautogui actions (seconds)
pyautogui.PAUSE = 0.3


# ──────────────────────────────────────────────
#  Application launching
# ──────────────────────────────────────────────

def open_application(app_name: str) -> bool:
    """
    Launch an application by its friendly name (e.g. "chrome", "notepad").

    Returns True if the app was found and launched, False otherwise.
    """
    app_name = app_name.lower().strip()
    path = APP_PATHS.get(app_name)

    if path and os.path.exists(path):
        subprocess.Popen([path])
        return True

    # Fallback: try running the name directly (works for many Windows apps)
    try:
        os.startfile(app_name)          # type: ignore[attr-defined]
        return True
    except OSError:
        return False


# ──────────────────────────────────────────────
#  Web searches
# ──────────────────────────────────────────────

def search_google(query: str) -> None:
    """Open the default browser and search Google for *query*."""
    url = GOOGLE_SEARCH_URL.format(query.replace(" ", "+"))
    webbrowser.open(url)


def search_youtube(query: str) -> None:
    """Open the default browser and search YouTube for *query*."""
    url = YOUTUBE_SEARCH_URL.format(query.replace(" ", "+"))
    webbrowser.open(url)


# ──────────────────────────────────────────────
#  Mouse & keyboard control
# ──────────────────────────────────────────────

def move_mouse(x: int, y: int) -> None:
    """Move the mouse cursor to absolute screen position (*x*, *y*)."""
    pyautogui.moveTo(x, y, duration=0.4)


def click_mouse(button: str = "left") -> None:
    """Click the mouse at the current position."""
    pyautogui.click(button=button)


def double_click_mouse() -> None:
    """Double-click the left mouse button at the current position."""
    pyautogui.doubleClick()


def scroll_mouse(clicks: int = 3) -> None:
    """Scroll the mouse wheel. Positive = up, negative = down."""
    pyautogui.scroll(clicks)


def press_key(key: str) -> None:
    """Press and release a single keyboard key (e.g. 'enter', 'escape')."""
    pyautogui.press(key)


def hotkey(*keys: str) -> None:
    """
    Press a keyboard shortcut.

    Example: hotkey('ctrl', 'c') for copy.
    """
    pyautogui.hotkey(*keys)


def type_text(text: str, interval: float = 0.03) -> None:
    """Type *text* character by character with a short interval."""
    pyautogui.typewrite(text, interval=interval)


def type_text_unicode(text: str) -> None:
    """
    Type arbitrary text (including Unicode) by writing to the clipboard
    and pasting. Works for all characters.
    """
    import pyperclip
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")


# ──────────────────────────────────────────────
#  Screenshots
# ──────────────────────────────────────────────

def take_screenshot() -> str:
    """
    Capture the entire screen and save it as a PNG.

    Returns the full path to the saved image.
    """
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(SCREENSHOT_DIR, f"screenshot_{timestamp}.png")
    img = pyautogui.screenshot()
    img.save(filepath)
    return filepath


# ──────────────────────────────────────────────
#  Volume control  (Windows)
# ──────────────────────────────────────────────

def volume_up(steps: int = 1) -> None:
    """Increase system volume by pressing Volume-Up *steps* times."""
    presses = max(1, steps * (VOLUME_STEP // 2))  # each key press ≈ 2 %
    for _ in range(presses):
        pyautogui.press("volumeup")


def volume_down(steps: int = 1) -> None:
    """Decrease system volume by pressing Volume-Down *steps* times."""
    presses = max(1, steps * (VOLUME_STEP // 2))
    for _ in range(presses):
        pyautogui.press("volumedown")


def volume_mute() -> None:
    """Toggle system mute."""
    pyautogui.press("volumemute")


# ──────────────────────────────────────────────
#  File / folder management
# ──────────────────────────────────────────────

def open_folder(path: str) -> bool:
    """Open a folder in Windows Explorer. Returns True on success."""
    path = os.path.expanduser(path)
    if os.path.isdir(path):
        os.startfile(path)              # type: ignore[attr-defined]
        return True
    return False


def open_file(path: str) -> bool:
    """Open a file with its default application. Returns True on success."""
    path = os.path.expanduser(path)
    if os.path.isfile(path):
        os.startfile(path)              # type: ignore[attr-defined]
        return True
    return False


# ──────────────────────────────────────────────
#  System power commands
# ──────────────────────────────────────────────

def shutdown_pc() -> None:
    """Shut down the computer immediately."""
    os.system("shutdown /s /t 5")


def restart_pc() -> None:
    """Restart the computer immediately."""
    os.system("shutdown /r /t 5")


def lock_pc() -> None:
    """Lock the workstation."""
    import ctypes
    ctypes.windll.user32.LockWorkStation()


def sleep_pc() -> None:
    """Put the computer to sleep."""
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
