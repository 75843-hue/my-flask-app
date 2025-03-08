from flask import Flask, request, jsonify

app = Flask(__name__)

# Homepage
@app.route("/")
def home():
    return "Hello from Render Flask!"

# Store pings in a list
silence_pings = []

# Receive silence pings from the microphone script
@app.route("/silence", methods=["POST"])
def silence_ping():
    global silence_pings
    data = request.json  # Get the incoming data
    silence_pings.append(data)  # Store it
    print("Received silence ping:", data)  # Show in logs
    return {"message": "Silence ping received"}, 200

# Show stored pings
@app.route("/get_pings", methods=["GET"])
def get_pings():
    return jsonify(silence_pings)  # Return all stored pings

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
