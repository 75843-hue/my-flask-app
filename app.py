from flask import Flask, request, jsonify

app = Flask(__name__)

# A list to store silence pings
silence_pings = []

@app.route("/")
def home():
    return "Hello from Render Flask!"

# This route will handle silence pings
@app.route("/silence", methods=["POST"])
def receive_silence():
    data = request.json  # Get the JSON data sent in the request
    if "status" in data and data["status"] == "silent":
        silence_pings.append("Silence detected")  # Save the ping
        return jsonify({"message": "Silence ping received!"}), 200
    return jsonify({"error": "Invalid data"}), 400

# This route will show all received silence pings
@app.route("/show_pings")
def show_pings():
    return jsonify({"pings": silence_pings})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
