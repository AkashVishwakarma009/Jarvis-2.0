"""
config.py - Configuration settings for the Jarvis AI Assistant.

Contains all configurable constants: assistant name, wake word,
application paths, volume step size, and speech engine settings.
"""

# ──────────────────────────────────────────────
#  Assistant identity
# ──────────────────────────────────────────────
ASSISTANT_NAME = "Jarvis"
WAKE_WORD = "hey mitra"                # Must be lowercase

# ──────────────────────────────────────────────
#  Speech-recognition settings
# ──────────────────────────────────────────────
RECOGNITION_ENERGY_THRESHOLD = 4000     # Ambient noise sensitivity
RECOGNITION_PAUSE_THRESHOLD = 1.0       # Seconds of silence before cut-off
RECOGNITION_TIMEOUT = 5                 # Max seconds to wait for speech start
RECOGNITION_PHRASE_LIMIT = 10           # Max seconds of speech per command

# ──────────────────────────────────────────────
#  Text-to-speech (pyttsx3) settings
# ──────────────────────────────────────────────
TTS_RATE = 175                          # Words per minute
TTS_VOLUME = 1.0                        # 0.0 – 1.0

# ──────────────────────────────────────────────
#  Application paths  (Windows defaults)
# ──────────────────────────────────────────────
APP_PATHS = {
    "chrome":   r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode":   r"C:\Users\Admin\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "notepad":  r"C:\Windows\System32\notepad.exe",
    "explorer": r"C:\Windows\explorer.exe",
    "calc":     r"C:\Windows\System32\calc.exe",
    "cmd":      r"C:\Windows\System32\cmd.exe",
}

# ──────────────────────────────────────────────
#  Volume control
# ──────────────────────────────────────────────
VOLUME_STEP = 10                        # Percentage change per step

# ──────────────────────────────────────────────
#  Screenshot settings
# ──────────────────────────────────────────────
SCREENSHOT_DIR = r"C:\Users\Admin\OneDrive\Desktop\new projects\Jarvic-2.0\screenshots"

# ──────────────────────────────────────────────
#  URLs
# ──────────────────────────────────────────────
GOOGLE_SEARCH_URL = "https://www.google.com/search?q={}"
YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={}"

# ──────────────────────────────────────────────
#  Scheduled reminders (24-hour format)
#  Each entry: (hour, minute, message)
# ──────────────────────────────────────────────
SCHEDULED_REMINDERS = [
    (13, 1, "Sir, lunch time ho gaya hai. Please take a break and have your meal."),
    (19, 0, "Sir, ghar jaane ka time ho gaya hai. Please apna kaam wrap up karein."),
]

# ──────────────────────────────────────────────
#  Avatar image
# ──────────────────────────────────────────────
AVATAR_IMAGE = r"assets/avatar.png"     # Relative to the jarvis/ directory
