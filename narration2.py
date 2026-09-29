
#
# Why narration used to stop after the first announcement:
#  Reusing one pyttsx3 engine and calling runAndWait() again and again
#  (especially from a background thread) is unreliable and often goes
#  silent after the first sentence. This version avoids that by speaking
#  with the operating system's own speech tool, launched fresh each time:
#     macOS   -> the built-in `say` command
#     Windows -> PowerShell + System.Speech (built in, no install needed)
#     other   -> pyttsx3 with a fresh engine per sentence
#
# Behaviour:
#  - speak() never blocks the YOLO thread
#  - speaks only when the message changes (2s minimum gap)
#  - stale messages are dropped so narration never lags the camera
#  - male = default voice, female = female voice (falls back gracefully)

import os
import platform
import queue
import subprocess
import threading
import time

MIN_GAP = 2.0  # seconds between two different announcements
_OS = platform.system()

_queue = queue.Queue(maxsize=1)
_lock = threading.Lock()
_last_message = ""
_last_speak_time = 0.0
_worker_started = False


def make_sentence(labels):
    unique = sorted(set(labels))
    if not unique:
        return "No objects detected"
    if len(unique) == 1:
        return f"{unique[0]} detected"
    if len(unique) == 2:
        return f"{unique[0]} and {unique[1]} detected"
    return ", ".join(unique[:-1]) + f", and {unique[-1]} detected"


# ---------------- macOS ----------------
def _say_mac(text, rate, voice_index):
    voice = "Samantha" if voice_index == 1 else "Alex"
    result = subprocess.run(["say", "-v", voice, "-r", str(int(rate)), text],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:  # voice not installed -> use system default
        subprocess.run(["say", "-r", str(int(rate)), text],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------- Windows ----------------
_PS_SCRIPT = (
    "Add-Type -AssemblyName System.Speech;"
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
    "try { $g = [Enum]::Parse([System.Speech.Synthesis.VoiceGender], $env:NARR_GENDER);"
    "$s.SelectVoiceByHints($g) } catch {};"
    "$s.Rate = [int]$env:NARR_RATE;"
    "$s.Speak($env:NARR_TEXT);"
)


def _say_windows(text, rate, voice_index):
    # Map words-per-minute (100-300) to SAPI rate (-10..10); 175 wpm ~ 0
    sapi_rate = max(-10, min(10, round((rate - 175) / 12.5)))
    env = os.environ.copy()
    env["NARR_TEXT"] = text            # passed via env so quotes can't break it
    env["NARR_RATE"] = str(sapi_rate)
    env["NARR_GENDER"] = "Female" if voice_index == 1 else "Male"
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_SCRIPT],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


# ---------------- Fallback (Linux etc.) ----------------
def _say_pyttsx3(text, rate, voice_index):
    import pyttsx3
    engine = pyttsx3.init()
    try:
        voices = engine.getProperty("voices")
        if len(voices) > voice_index:
            engine.setProperty("voice", voices[voice_index].id)
        engine.setProperty("rate", rate)
        engine.say(text)
        engine.runAndWait()
    finally:
        try:
            engine.stop()
        except Exception:
            pass
        del engine


def _speak_now(text, rate, voice_index):
    if _OS == "Darwin":
        _say_mac(text, rate, voice_index)
    elif _OS == "Windows":
        _say_windows(text, rate, voice_index)
    else:
        _say_pyttsx3(text, rate, voice_index)


def _worker():
    while True:
        text, rate, voice_index = _queue.get()
        try:
            _speak_now(text, rate, voice_index)
        except Exception as e:
            print(f"[AUDIO ERROR]: {e}")


def speak(text, rate=160, voice_index=0):
    """Non-blocking. Queues text only if it is new and the gap has passed."""
    global _last_message, _last_speak_time, _worker_started

    now = time.time()
    with _lock:
        if not _worker_started:
            threading.Thread(target=_worker, daemon=True).start()
            _worker_started = True
        if text == _last_message or now - _last_speak_time < MIN_GAP:
            return
        _last_message = text
        _last_speak_time = now

    try:
        _queue.get_nowait()  # drop any stale pending message
    except queue.Empty:
        pass
    try:
        _queue.put_nowait((text, rate, voice_index))
    except queue.Full:
        pass
