import pyaudio
import numpy as np
import time
import requests
from datetime import datetime

# CONFIGURABLE SETTINGS
INITIAL_CALIBRATION_TIME = 10  # seconds to calibrate ambient noise
RECALIBRATION_CHECK_INTERVAL = 60  # re-check environment every 60s
CALIBRATION_SENSITIVITY_FACTOR = 1.2  # threshold = avg_noise * this factor
SILENCE_DURATION_THRESHOLD = 3  # must be silent >= 3s
CHECK_INTERVAL = 1  # check audio every 1s
RECALIBRATION_THRESHOLD_FACTOR = 1.5  # if environment changes > 50%, re-calibrate

# Your Render endpoint (already integrated):
SERVER_URL = "https://my-flask-app-ge3j.onrender.com/silence"

p = None
stream = None

silence_start_time = None
is_silent = False
silence_threshold = None
last_calibration_time = None
recent_volume_levels = []

def start_mic_stream():
    """Initializes or restarts the microphone stream."""
    global p, stream
    if p is not None:
        p.terminate()

    while True:
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=44100,
                            input=True,
                            frames_per_buffer=1024)
            print("[INFO] Microphone stream started successfully.")
            return
        except Exception as e:
            print(f"[ERROR] Could not access microphone: {e}. Retrying in 2 seconds...")
            time.sleep(2)

def calibrate_silence_threshold(duration=10):
    """Calibrates the silence threshold by sampling audio for 'duration' seconds."""
    print(f"[INFO] Calibrating silence threshold for {duration} seconds. Please remain quiet if possible.")
    global stream

    volume_levels = []
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
            volume = np.abs(data).mean()
            volume_levels.append(volume)
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"[ERROR] Mic read error during calibration: {e}")
            start_mic_stream()

    avg_noise = np.mean(volume_levels) if volume_levels else 0
    threshold = avg_noise * CALIBRATION_SENSITIVITY_FACTOR
    print(f"[INFO] Initial average noise: {avg_noise:.2f}, threshold set to: {threshold:.2f}")
    return threshold

def read_volume_level():
    """Reads audio data and returns the current volume level. Restarts mic if error."""
    global p, stream
    try:
        data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
        return np.abs(data).mean()
    except Exception as e:
        print(f"[ERROR] Mic read error: {e}. Restarting microphone stream...")
        start_mic_stream()
        return -1

def send_silence_ping(status_type, start_time, end_time=None):
    """
    Sends either:
      - "silence_start" ping (start_time only)
      - "silence_end" ping (start_time, end_time, duration)
    """
    payload = {
        "status": status_type,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if status_type == "silence_end" and end_time:
        duration = round((end_time - start_time).total_seconds(), 2)
        payload["end_time"] = end_time.strftime("%Y-%m-%d %H:%M:%S")
        payload["duration"] = duration

    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"[INFO] Sent {status_type} ping: {payload}, response code: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to send {status_type} ping: {e}")

def maybe_recalibrate():
    """Checks if environment changed drastically, triggers short calibration if so."""
    global silence_threshold, last_calibration_time, recent_volume_levels

    if len(recent_volume_levels) < 20:
        return

    current_avg = np.mean(recent_volume_levels)
    if current_avg > 0:
        # If environment is significantly quieter
        if (current_avg * CALIBRATION_SENSITIVITY_FACTOR * RECALIBRATION_THRESHOLD_FACTOR) < silence_threshold:
            print("[INFO] Environment significantly quieter. Recalibrating threshold...")
            silence_threshold = calibrate_silence_threshold(5)
        # If environment is significantly louder
        elif current_avg * CALIBRATION_SENSITIVITY_FACTOR > silence_threshold * RECALIBRATION_THRESHOLD_FACTOR:
            print("[INFO] Environment significantly louder. Recalibrating threshold...")
            silence_threshold = calibrate_silence_threshold(5)

    recent_volume_levels = []

def main():
    global is_silent, silence_start_time, silence_threshold, last_calibration_time

    # Start mic and calibrate
    start_mic_stream()
    silence_threshold = calibrate_silence_threshold(INITIAL_CALIBRATION_TIME)
    last_calibration_time = time.time()

    print("[INFO] Silence monitor running. Waiting for silence to start or end...")

    while True:
        volume_level = read_volume_level()
        if volume_level < 0:
            time.sleep(CHECK_INTERVAL)
            continue

        recent_volume_levels.append(volume_level)

        # Check if environment changed drastically
        if (time.time() - last_calibration_time) > RECALIBRATION_CHECK_INTERVAL:
            maybe_recalibrate()
            last_calibration_time = time.time()

        print(f"DEBUG: Current volume level: {volume_level:.2f}, Threshold: {silence_threshold:.2f}")

        if volume_level < silence_threshold:
            # Silence detected
            if not is_silent:
                silence_start_time = datetime.now()
                is_silent = True
                print(f"[INFO] Silence started at {silence_start_time.strftime('%H:%M:%S')}")
                # Optionally store the moment silence began:
                send_silence_ping("silence_start", silence_start_time)
        else:
            # Noise detected
            if is_silent:
                # Silence ended
                silence_end_time = datetime.now()
                total_silence = (silence_end_time - silence_start_time).total_seconds()
                if total_silence >= SILENCE_DURATION_THRESHOLD:
                    send_silence_ping("silence_end", silence_start_time, silence_end_time)
                    print(f"[INFO] Silence ended at {silence_end_time.strftime('%H:%M:%S')}, lasted {round(total_silence, 2)}s")
                else:
                    print(f"[INFO] Silence was too short ({round(total_silence, 2)}s), not sending ping.")
                is_silent = False

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
