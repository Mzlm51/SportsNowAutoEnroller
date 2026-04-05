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
        request_date = data["start"][:10]

        class_start = datetime.fromisoformat(data["start"])
        if class_start.tzinfo is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        if class_start < now:
            return jsonify({"status": "error", "message": "This class has already passed."}), 400

        if any(r["start"][:10] == request_date for r in requests_list):
            return jsonify({"status": "error", "message": f"Already scheduled on {request_date}!"}), 400

        try:
            with open("enroll_log.json") as f:
                log = json.load(f)
        except (FileNotFoundError, ValueError):
            log = []
        if any(l["start"][:10] == request_date for l in log):
            return jsonify({"status": "error", "message": f"Already enrolled on {request_date}!"}), 400

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

@app.route("/unenroll_requests", methods=["GET", "POST", "DELETE"])
def unenroll_requests():
    try:
        with open("unenroll_requests.json") as f:
            queue = json.load(f)
    except (FileNotFoundError, ValueError):
        queue = []

    if request.method == "GET":
        return jsonify(queue)

    if request.method == "POST":
        data = request.json
        queue.append({"title": data["title"], "start": data["start"], "requested_at": datetime.now().isoformat()})
        with open("unenroll_requests.json", "w") as f:
            json.dump(queue, f, indent=2)
        return jsonify({"status": "ok"})

    if request.method == "DELETE":
        data = request.json
        queue = [r for r in queue if not (r["title"] == data["title"] and r["start"] == data["start"])]
        with open("unenroll_requests.json", "w") as f:
            json.dump(queue, f, indent=2)
        return jsonify({"status": "ok"})

@app.route("/cancelled_classes", methods=["GET"])
def cancelled_classes():
    try:
        with open("cancelled_classes.json") as f:
            return jsonify(json.load(f))
    except (FileNotFoundError, ValueError):
        return jsonify([])

@app.route("/enroll_log", methods=["GET"])
def enroll_log():
    try:
        with open("enroll_log.json") as f:
            return jsonify(json.load(f))
    except (FileNotFoundError, ValueError):
        return jsonify([])

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