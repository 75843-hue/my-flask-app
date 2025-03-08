import pyaudio
import numpy as np
import time
import requests
from datetime import datetime

# Configurable settings
THRESHOLD = 500  # Adjust for sensitivity to speech vs. background noise
SILENCE_DURATION_THRESHOLD = 3  # Seconds of silence before it's considered "true silence"
CHECK_INTERVAL = 1  # How often to check for silence (in seconds)
SERVER_URL = "https://my-flask-app-ge3j.onrender.com"  # Replace with your actual server URL

# Setup microphone
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

# Silence tracking variables
silence_start_time = None
is_silent = False  # Tracks the current silence state

def is_silence():
    """Check if the audio input is below the silence threshold"""
    data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
    return np.abs(data).mean() < THRESHOLD

def send_silence_ping(start_timestamp, end_timestamp=None):
    """Send silence start and end pings to the server"""
    payload = {"status": "silent", "start_time": start_timestamp}
    
    if end_timestamp:
        duration = round((end_timestamp - start_timestamp).total_seconds(), 2)
        payload["end_time"] = end_timestamp
        payload["duration"] = duration
    
    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"Sent silence ping: {payload}, Response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send silence ping: {e}")

print("Silence monitor running...")

while True:
    if is_silence():
        if not is_silent:  # First moment of detected silence
            silence_start_time = datetime.now()
            is_silent = True
    else:
        if is_silent:  # Silence has ended
            silence_end_time = datetime.now()
            send_silence_ping(silence_start_time, silence_end_time)
            is_silent = False  # Reset silence state
    
    time.sleep(CHECK_INTERVAL)
