import pyaudio
import numpy as np
import time
import requests
from datetime import datetime

# Configurable settings
CALIBRATION_TIME = 5  # Seconds to calibrate ambient noise
SILENCE_DURATION_THRESHOLD = 3  # Seconds before silence is considered real
CHECK_INTERVAL = 1  # How often to check for silence (in seconds)
SERVER_URL = "https://my-flask-app-ge3j.onrender.com/silence"  # Render Flask App

# Setup microphone
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

# Auto-adjust silence threshold
print("🔄 Calibrating silence threshold... please wait.")
threshold_values = []
for _ in range(int(CALIBRATION_TIME / CHECK_INTERVAL)):
    data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
    threshold_values.append(np.abs(data).mean())
    time.sleep(CHECK_INTERVAL)

SILENCE_THRESHOLD = np.mean(threshold_values) * 1.2  # Set silence threshold slightly higher
print(f"✅ Silence threshold set to: {SILENCE_THRESHOLD:.2f}")

# Silence tracking variables
silence_start_time = None
is_silent = False

def is_silence():
    """Check if the current audio input level is below the threshold"""
    data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
    volume_level = np.abs(data).mean()
    print(f"DEBUG: Current volume level: {volume_level:.2f}")
    return volume_level < SILENCE_THRESHOLD

def send_silence_ping(start_timestamp, end_timestamp=None):
    """Send silence start and end pings to the server"""
    payload = {
        "status": "silent",
        "start_time": start_timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Convert datetime to string
    }
    
    if end_timestamp:
        duration = round((end_timestamp - start_timestamp).total_seconds(), 2)
        payload["end_time"] = end_timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Convert datetime to string
        payload["duration"] = duration

    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"📡 Sent silence ping: {payload}, Response: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Failed to send silence ping: {e}")

print("🎤 Silence monitor running...")

while True:
    if is_silence():
        if not is_silent:  # First moment of detected silence
            silence_start_time = datetime.now()
            is_silent = True
            print(f"🤫 Silence started at {silence_start_time.strftime('%H:%M:%S')}")
    else:
        if is_silent:  # Silence has ended
            silence_end_time = datetime.now()
            send_silence_ping(silence_start_time, silence_end_time)
            is_silent = False  # Reset silence state
            print(f"🗣️ Sound detected at {silence_end_time.strftime('%H:%M:%S')}")

    time.sleep(CHECK_INTERVAL)
