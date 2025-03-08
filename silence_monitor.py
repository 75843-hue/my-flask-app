import requests
import time
import pyaudio
import numpy as np

# REPLACE THIS with the actual URL from Replit once you have it running
SERVER_URL = "https://my-flask-app-ge3j.onrender.com"

# Sensitivity settings
THRESHOLD = 300  # Lower = more sensitive to noise, higher = less sensitive
SILENCE_SECONDS = 60  # How long you need to be silent for it to trigger
CHECK_INTERVAL = 2  # How often to check (in seconds)

# Set up microphone
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

silent_time = 0

def is_silent():
    data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
    return np.abs(data).mean() < THRESHOLD

def send_silence_ping():
    try:
        response = requests.post(SERVER_URL, json={"status": "silent"})
        print(f"Silence ping sent. Response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send silence ping: {e}")

print("Silence monitor running...")

while True:
    if is_silent():
        silent_time += CHECK_INTERVAL
        if silent_time >= SILENCE_SECONDS:
            send_silence_ping()
            silent_time = 0  # Reset after sending ping
    else:
        silent_time = 0  # Reset if noise detected

    time.sleep(CHECK_INTERVAL)
