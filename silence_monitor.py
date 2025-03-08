import requests
import time

# Change this to your actual Render URL
SERVER_URL = "https://my-flask-app-ge3j.onrender.com/silence"

def send_silence_ping():
    try:
        response = requests.post(SERVER_URL, json={"status": "silent"})
        print(f"Silence ping sent. Response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send silence ping: {e}")

print("Silence monitor running...")

while True:
    send_silence_ping()
    time.sleep(10)  # Send a silence ping every 10 seconds
