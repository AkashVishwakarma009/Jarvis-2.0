"""
speech_engine.py - Voice I/O for the Jarvis AI Assistant.

Provides two core capabilities:
  • listen()  – capture and transcribe speech from the microphone.
  • speak()   – convert text to audible speech via pyttsx3.
"""

import speech_recognition as sr
import pyttsx3

from config import (
    ASSISTANT_NAME,
    RECOGNITION_ENERGY_THRESHOLD,
    RECOGNITION_PAUSE_THRESHOLD,
    RECOGNITION_TIMEOUT,
    RECOGNITION_PHRASE_LIMIT,
    TTS_RATE,
    TTS_VOLUME,
)

# ──────────────────────────────────────────────
#  Initialise the text-to-speech engine (once)
# ──────────────────────────────────────────────
_engine = pyttsx3.init()
_engine.setProperty("rate", TTS_RATE)
_engine.setProperty("volume", TTS_VOLUME)

# Try to pick a female English voice (Zira)
_voices = _engine.getProperty("voices")
for _v in _voices:
    if "zira" in _v.name.lower():
        _engine.setProperty("voice", _v.id)
        break
else:
    # Fallback: pick any female / English voice
    for _v in _voices:
        if "female" in _v.name.lower() or "english" in _v.name.lower():
            _engine.setProperty("voice", _v.id)
            break


def speak(text: str) -> None:
    """Convert *text* to speech and play it through the speakers."""
    print(f"[{ASSISTANT_NAME}] {text}")
    _engine.say(text)
    _engine.runAndWait()


# ──────────────────────────────────────────────
#  Initialise the speech recogniser
# ──────────────────────────────────────────────
_recognizer = sr.Recognizer()
_recognizer.energy_threshold = RECOGNITION_ENERGY_THRESHOLD
_recognizer.pause_threshold = RECOGNITION_PAUSE_THRESHOLD


def listen(prompt: str | None = None) -> str:
    """
    Listen through the default microphone and return the recognised text
    (lowercased).  Returns an empty string on failure.

    Parameters
    ----------
    prompt : str, optional
        If given, Jarvis will speak this text before listening.
    """
    if prompt:
        speak(prompt)

    with sr.Microphone() as source:
        print("Listening ...")
        try:
            audio = _recognizer.listen(
                source,
                timeout=RECOGNITION_TIMEOUT,
                phrase_time_limit=RECOGNITION_PHRASE_LIMIT,
            )
        except sr.WaitTimeoutError:
            return ""

    try:
        text = _recognizer.recognize_google(audio)
        print(f"[You] {text}")
        return text.lower()
    except sr.UnknownValueError:
        # Speech was unintelligible
        return ""
    except sr.RequestError as exc:
        print(f"[Error] Google Speech Recognition service error: {exc}")
        return ""
