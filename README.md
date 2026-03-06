# Jarvis 2.0 — AI Voice Assistant for Windows

A fully voice-controlled PC assistant built with Python. Say **"Hey Jarvis"** to activate, then give a command.

---

## Project Structure

```
Jarvic-2.0/
├── requirements.txt        # Python dependencies
├── README.md               # You are here
└── jarvis/
    ├── main.py             # Entry point — run this file
    ├── config.py           # All configurable settings
    ├── speech_engine.py    # Voice recognition & text-to-speech
    ├── commands.py         # Command router (keyword → action)
    └── automation.py       # Low-level PC automation helpers
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.10+** | [python.org](https://www.python.org/downloads/) |
| **Microphone** | Any USB / built-in mic |
| **Internet** | Required for Google Speech Recognition |
| **Windows 10/11** | OS-specific commands are used |

---

## Installation

```bash
# 1. Clone or navigate to the project folder
cd "Jarvic-2.0"

# 2. (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (First time only) PyAudio may need a manual install on Windows:
pip install pipwin
pipwin install pyaudio
```

> **Note:** If `pipwin` doesn't work, download the PyAudio `.whl` for your Python version from  
> https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio  
> and install with `pip install <filename>.whl`.

---

## Running the Assistant

```bash
cd jarvis
python main.py
```

1. Jarvis greets you with a time-appropriate message.  
2. Say **"Hey Jarvis"** — he acknowledges and starts listening.  
3. Speak your command (see list below).  
4. Jarvis executes it and returns to passive listening.

Press **Ctrl + C** at any time to quit.

---

## Supported Commands

### Applications
| Say | Action |
|---|---|
| "Open Chrome" | Launches Google Chrome |
| "Open VS Code" | Launches Visual Studio Code |
| "Open Notepad" | Launches Notepad |
| "Open Calculator" | Launches Calculator |
| "Open Command Prompt" | Launches CMD |
| "Open File Explorer" | Launches Explorer |

### Web Search
| Say | Action |
|---|---|
| "Search Google for Python tutorials" | Opens Google results |
| "Search YouTube for lo-fi music" | Opens YouTube results |

### Typing & Clipboard
| Say | Action |
|---|---|
| "Type hello world" | Types text at the cursor |
| "Copy" / "Paste" | Ctrl+C / Ctrl+V |
| "Select all" | Ctrl+A |
| "Undo" / "Redo" | Ctrl+Z / Ctrl+Y |
| "Save" | Ctrl+S |

### Mouse Control
| Say | Action |
|---|---|
| "Click" / "Right click" | Mouse clicks |
| "Double click" | Double left-click |
| "Scroll up" / "Scroll down" | Scroll wheel |

### Window Management
| Say | Action |
|---|---|
| "Close window" | Alt+F4 |
| "Minimize" / "Maximize" | Win+Down / Win+Up |
| "Switch window" | Alt+Tab |

### Screenshots
| Say | Action |
|---|---|
| "Take a screenshot" | Saves PNG to `screenshots/` |

### Volume
| Say | Action |
|---|---|
| "Volume up" / "Volume down" | Adjusts system volume |
| "Mute" | Toggles mute |

### Files & Folders
| Say | Action |
|---|---|
| "Open folder C:\Users" | Opens in Explorer |
| "Open file C:\notes.txt" | Opens with default app |

### System
| Say | Action |
|---|---|
| "Shutdown" | Shuts down PC (with confirmation) |
| "Restart" | Restarts PC (with confirmation) |
| "Lock computer" | Locks the workstation |
| "Sleep" | Puts PC to sleep |

### Misc
| Say | Action |
|---|---|
| "What time is it" | Speaks the current time |
| "What's the date" | Speaks today's date |
| "Goodbye" / "Exit" | Exits the assistant |

---

## Configuration

Edit **`jarvis/config.py`** to customise:

- `WAKE_WORD` — change the activation phrase  
- `APP_PATHS` — add or modify application paths  
- `TTS_RATE` — speech speed (words per minute)  
- `VOLUME_STEP` — how much each volume command changes  
- `SCREENSHOT_DIR` — where screenshots are saved  

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Could not find PyAudio" | `pip install pipwin && pipwin install pyaudio` |
| Mic not detected | Check default input device in Windows Sound settings |
| Commands not recognised | Speak clearly; check `RECOGNITION_ENERGY_THRESHOLD` in config |
| App won't open | Verify the path in `APP_PATHS` matches your installation |

---

## License

This project is provided as-is for personal and educational use.
