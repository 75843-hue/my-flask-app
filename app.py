from flask import Flask, request

app = Flask(__name__)

# Real-time in-memory list for incoming pings
silence_data = []

# Frozen snapshot for the AI
frozen_silence_data = []

@app.route("/")
def home():
    return (
        "Hello from Render Flask!<br>"
        "Use /show_pings_text for real-time text data (newest first).<br>"
        "Use /freeze_pings to finalize a snapshot, then /show_frozen_pings_text to see it."
    )

@app.route("/silence", methods=["POST"])
def receive_silence():
    """
    Expects JSON like:
      {
        'status': 'silence_start' or 'silence_end',
        'start_time': 'YYYY-MM-DD HH:MM:SS',
        'end_time': optional (if silence_end),
        'duration': optional (if silence_end)
      }
    Sent by your silence_monitor.py script.
    """
    data = request.json
    silence_data.append(data)
    print(f"[SERVER] Received ping: {data}")
    return "Silence event recorded", 200

@app.route("/show_pings_text", methods=["GET"])
def show_pings_text():
    """
    Shows the real-time data in plain text, newest entries on top.
    This is a real-time view that changes if new pings arrive.
    """
    lines = []
    lines.append("REAL-TIME SILENCE DATA (NEWEST FIRST):\n")

    # Reverse so the newest entries appear first
    reversed_data = list(reversed(silence_data))
    
    for entry in reversed_data:
        status = entry.get("status", "unknown")
        start_time = entry.get("start_time", "N/A")
        
        if status == "silence_start":
            lines.append(f"Silence START at {start_time}")
        elif status == "silence_end":
            end_time = entry.get("end_time", "N/A")
            duration = entry.get("duration", "N/A")
            lines.append(f"Silence END at {end_time}")
            lines.append(f"  Started: {start_time}")
            lines.append(f"  Duration: {duration} seconds")
        else:
            lines.append(f"Unknown status: {entry}")
        
        lines.append("---")
    
    return "<pre>" + "\n".join(lines) + "</pre>"

@app.route("/freeze_pings", methods=["GET", "POST"])
def freeze_pings():
    """
    Copies the current real-time data (silence_data) into frozen_silence_data,
    creating a static snapshot that won't change even if new pings arrive later.
    """
    global frozen_silence_data
    # Make a copy of the current list
    frozen_silence_data = list(silence_data)
    print("[SERVER] Data has been frozen.")
    return "Data has been frozen. Visit /show_frozen_pings_text to see the snapshot."

@app.route("/show_frozen_pings_text", methods=["GET"])
def show_frozen_pings_text():
    """
    Shows the FROZEN snapshot in plain text, newest entries on top.
    This data does NOT update once frozen, so the AI sees a static snapshot.
    """
    lines = []
    lines.append("FROZEN SILENCE DATA (NEWEST FIRST):\n")

    reversed_data = list(reversed(frozen_silence_data))
    
    for entry in reversed_data:
        status = entry.get("status", "unknown")
        start_time = entry.get("start_time", "N/A")
        
        if status == "silence_start":
            lines.append(f"Silence START at {start_time}")
        elif status == "silence_end":
            end_time = entry.get("end_time", "N/A")
            duration = entry.get("duration", "N/A")
            lines.append(f"Silence END at {end_time}")
            lines.append(f"  Started: {start_time}")
            lines.append(f"  Duration: {duration} seconds")
        else:
            lines.append(f"Unknown status: {entry}")
        
        lines.append("---")
    
    return "<pre>" + "\n".join(lines) + "</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
