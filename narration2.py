# Made it Linux friendly

import pyttsx3
import time

# Initialize the engine once
engine = pyttsx3.init()
last_message = ""
last_speak_time = 0

def make_sentence(labels):
    unique = sorted(list(set(labels)))
    if not unique: return "No objects detected"
    if len(unique) == 1: return f"{unique[0]} detected"
    return ", ".join(unique[:-1]) + f", and {unique[-1]} detected"

def speak(text, rate=160, voice_index=1):
    """Uses pyttsx3 for offline, low-latency narration with voice switching[cite: 1, 13]."""
    global last_message, last_speak_time
    current_time = time.time()

    # Cooldown to prevent overlapping speech[cite: 11]
    if text == last_message and (current_time - last_speak_time < 2):
        return

    last_message = text
    last_speak_time = current_time

    try:
        # 1. Set Rate (Speed)
        engine.setProperty('rate', rate)

        # 2. Set Voice (0 for Male, 1 for Female usually)
        voices = engine.getProperty('voices')
        if len(voices) > voice_index:
            engine.setProperty('voice', voices[voice_index].id)

        # 3. Speak
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        print(f"[AUDIO ERROR]: {e}")