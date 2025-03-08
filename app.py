from flask import Flask, request, jsonify

app = Flask(__name__)

# Stores all silence pings in memory
silence_data = []

@app.route("/")
def home():
    return "Hello from Render Flask! Visit /show_pings to see recorded silence events."

@app.route("/silence", methods=["POST"])
def receive_silence():
    """
    Expects JSON like:
      {
        "status": "silence_start" or "silence_end",
        "start_time": "YYYY-MM-DD HH:MM:SS",
        "end_time": optional,
        "duration": optional
      }
    """
    data = request.json
    silence_data.append(data)
    print(f"[SERVER] Received ping: {data}")
    return jsonify({"message": "Silence event recorded"}), 200

@app.route("/show_pings", methods=["GET"])
def show_pings():
    """Returns all stored silence events in an AI-readable format (plain text)."""
    if not silence_data:
        return "No silence events recorded yet."

    output = ["Silence Monitoring Log:\n"]

    for entry in silence_data:
        if entry["status"] == "silence_start":
            output.append(f"- Silence started at {entry['start_time']}")
        elif entry["status"] == "silence_end":
            output.append(f"- Silence ended at {entry['end_time']} (Lasted {entry['duration']} seconds)")

    return "<br>".join(output)  # Converts to readable HTML format

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
