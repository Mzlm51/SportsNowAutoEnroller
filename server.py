from flask import Flask, request, jsonify, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__)
FILE_PATH = os.path.join(os.path.dirname(__file__), "enroll_requests.json")
ENROLL_FILE = os.path.join(os.path.dirname(__file__), "enroll_requests.json")
SCHEDULER_FILE = "scheduler_status.json"

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/classes")
def classes():
    with open("classes.json") as f:
        return jsonify(json.load(f))
    
@app.route("/enroll_requests", methods=["GET", "POST", "DELETE"])
def enroll_requests():
    
    requests_list = []
    if os.path.exists(ENROLL_FILE):
        try:
            with open(ENROLL_FILE) as f:
                requests_list = json.load(f)
        except json.JSONDecodeError:
            requests_list = []

    if request.method == "GET":
        return jsonify(requests_list)

    if request.method == "POST":
        data = request.json

        if any(r["day"] == data["day"] for r in requests_list):
            return jsonify({"status": "error", "message": f"Already enrolled on {data['day']}!"}), 400

        requests_list.append({
            "title": data["title"],
            "start": data["start"],
            "href": data["href"],
            "day": data["day"],
            "requested_at": datetime.now().isoformat()
        })

        with open(ENROLL_FILE, "w") as f:
            json.dump(requests_list, f, indent=2)

        return jsonify({"status": "ok"})

    if request.method == "DELETE":
        data = request.json
        requests_list = [r for r in requests_list if not (r["title"] == data["title"] and r["day"] == data["day"])]

        with open(ENROLL_FILE, "w") as f:
            json.dump(requests_list, f, indent=2)

        return jsonify({"status": "ok"})

@app.route("/scheduler_status", methods=["GET", "POST"])
def scheduler_status():
    if request.method == "GET":
        try:
            with open(SCHEDULER_FILE) as f:
                status = json.load(f)
        except FileNotFoundError:
            status = {"enabled": False}
        return jsonify(status)

    elif request.method == "POST":
        data = request.json
        try:
            with open(SCHEDULER_FILE) as f:
                current = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            current = {"enabled": False, "autoscrape_enabled": False}
        current.update({k: v for k, v in data.items() if k in ("enabled", "autoscrape_enabled")})
        with open(SCHEDULER_FILE, "w") as f:
            json.dump(current, f)
        return jsonify({"status": "ok"})

if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000)