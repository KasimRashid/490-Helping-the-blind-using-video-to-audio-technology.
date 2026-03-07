import subprocess
import time

last_message = ""
last_speak_time = 0


def make_sentence(labels):
    unique = []

    for label in labels:
        if label not in unique:
            unique.append(label)

    unique.sort()

    if len(unique) == 0:
        return "No objects detected"

    if len(unique) == 1:
        return unique[0] + " detected"

    if len(unique) == 2:
        return unique[0] + " and " + unique[1] + " detected"

    sentence = ""

    for i in range(len(unique)):
        if i == len(unique) - 1:
            sentence += "and " + unique[i]
        else:
            sentence += unique[i] + ", "

    sentence += " detected"

    return sentence


def speak(text):
    global last_message, last_speak_time

    current_time = time.time()

    if text == last_message:
        return

    if current_time - last_speak_time < 2:
        return

    last_message = text
    last_speak_time = current_time

    print("[AUDIO]:", text)

    command = [
        "powershell",
        "-Command",
        f'Add-Type -AssemblyName System.Speech; '
        f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        f'$speak.Speak("{text}")'
    ]

    subprocess.Popen(command)