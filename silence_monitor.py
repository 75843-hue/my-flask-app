import pyaudio
import numpy as np
import time
import requests
from datetime import datetime

# 🔹 Configurable settings
SILENCE_DURATION_THRESHOLD = 3  # Seconds of silence before it's considered "true silence"
CHECK_INTERVAL = 1  # How often to check for silence (in seconds)
SERVER_URL = "https://my-flask-app-ge3j.onrender.com/silence"  # ✅ Correct server

# 🔹 Initialize PyAudio
p = None
stream = None

def start_mic_stream():
    """Ensures the microphone stream is always active"""
    global p, stream  # ✅ Declare global variables before use

    if p is not None:
        p.terminate()  # Make sure to properly restart

    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        print("[INFO] 🎤 Microphone stream started successfully.")
    except Exception as e:
        print(f"[ERROR] ❌ Failed to access microphone: {e}")
        time.sleep(2)  # Wait and retry
        start_mic_stream()

def calibrate_silence_threshold(duration=5):
    """Calibrates background noise level for better silence detection"""
    print("[INFO] 🔄 Calibrating silence threshold... please wait.")
    global stream

    volume_levels = []
    for _ in range(int(duration / CHECK_INTERVAL)):
        data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
        volume_levels.append(np.abs(data).mean())
        time.sleep(CHECK_INTERVAL)

    threshold = np.mean(volume_levels) * 1.2  # 20% above background noise
    print(f"[INFO] ✅ Silence threshold set to: {threshold:.2f}")
    return threshold

def is_silence(threshold):
    """Checks if the audio input is below the calculated silence threshold"""
    global stream
    try:
        data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
        volume_level = np.abs(data).mean()
        print(f"DEBUG: 🎚️ Current volume level: {volume_level:.2f}")  # Debugging info
        return volume_level < threshold
    except Exception as e:
        print(f"[ERROR] ❌ Issue reading microphone data: {e}")
        start_mic_stream()  # Restart mic if there's an error
        return False

def send_silence_ping(start_timestamp, end_timestamp=None):
    """Sends silence start and end pings to the server"""
    payload = {
        "status": "silent",
        "start_time": start_timestamp.isoformat()  # ✅ Fix: Convert datetime to JSON serializable format
    }
    
    if end_timestamp:
        duration = round((end_timestamp - start_timestamp).total_seconds(), 2)
        payload["end_time"] = end_timestamp.isoformat()
        payload["duration"] = duration
    
    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"[INFO] 📡 Sent silence ping: {payload}, Response: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] ❌ Failed to send silence ping: {e}")

# 🔹 Start microphone and calibrate
start_mic_stream()
silence_threshold = calibrate_silence_threshold()

# 🔹 Silence tracking variables
silence_start_time = None
is_silent = False  

print("[INFO] 🎤 Silence monitor running...")

while True:
    if is_silence(silence_threshold):
        if not is_silent:  # First moment of detected silence
            silence_start_time = datetime.now()
            is_silent = True
            print(f"[INFO] 🤫 Silence detected at {silence_start_time.strftime('%H:%M:%S')}")

    else:
        if is_silent:  # Silence has ended
            silence_end_time = datetime.now()
            send_silence_ping(silence_start_time, silence_end_time)
            print(f"[INFO] 🗣️ Sound detected at {silence_end_time.strftime('%H:%M:%S')}, silence lasted {round((silence_end_time - silence_start_time).total_seconds(), 2)} sec.")
            is_silent = False  

    time.sleep(CHECK_INTERVAL)
