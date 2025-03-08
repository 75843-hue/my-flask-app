from flask import Flask, request, jsonify

app = Flask(__name__)

# Stores all silence pings in memory
# Example entries:
# {
#   "status": "silence_start",
#   "start_time": "2025-03-08 12:00:00"
# }
# or
# {
#   "status": "silence_end",
#   "start_time": "2025-03-08 12:00:00",
#   "end_time": "2025-03-08 12:00:05",
#   "duration": 5.0
# }
silence_data = []

@app.route("/")
def home():
    return "Hello from Render Flask! Visit /show_pings to see stored silence events."

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
    """Returns all stored silence events in JSON format."""
    return jsonify(silence_data)

if __name__ == "__main__":
    # For local testing on port 5000, but on Render the port is set automatically
    app.run(host="0.0.0.0", port=5000, debug=True)
