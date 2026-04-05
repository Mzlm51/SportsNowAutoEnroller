import json, datetime, subprocess, time, logging
import sys

logging.basicConfig(level=logging.INFO)

ENROLL_FILE = "enroll_requests.json"
CHECK_INTERVAL = 5
HOURS_AHEAD = 48

scraped_class_keys = set()


def scheduler_enabled():
    try:
        with open("scheduler_status.json") as f:
            status = json.load(f)
            return status.get("enabled", False)
    except FileNotFoundError:
        return False

def autoscrape_enabled():
    try:
        with open("scheduler_status.json") as f:
            status = json.load(f)
            return status.get("autoscrape_enabled", False)
    except FileNotFoundError:
        return False

def get_requests_to_enroll():
    now = datetime.datetime.now()
    cutoff = now + datetime.timedelta(hours=HOURS_AHEAD)

    try:
        with open(ENROLL_FILE) as f:
            requests = json.load(f)
    except FileNotFoundError:
        requests = []

    to_enroll = []
    for r in requests:
        class_start = datetime.datetime.fromisoformat(r["start"])
        if class_start.tzinfo is not None:
            class_start = class_start.astimezone().replace(tzinfo=None)
        if now <= class_start <= cutoff:
            to_enroll.append(r)
    return to_enroll

def should_scrape_after_class():
    now = datetime.datetime.now()
    try:
        with open("classes.json") as f:
            classes = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return False

    for cls in classes:
        start = datetime.datetime.fromisoformat(cls["start"])
        key = cls["start"]
        if start <= now <= start + datetime.timedelta(minutes=2) and key not in scraped_class_keys:
            scraped_class_keys.add(key)
            return True

    return False


def get_unenroll_requests():
    try:
        with open("unenroll_requests.json") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return []

def main():
    while True:
        if should_scrape_after_class() and autoscrape_enabled():
            logging.info("Initializing webscrape")
            try:
                subprocess.run([sys.executable, "main.py"], check=True)
            except Exception as e:
                logging.info("Scrape failed")

        if scheduler_enabled():
            to_enroll = get_requests_to_enroll()
            if to_enroll:
                logging.info(f"Found {len(to_enroll)} classes to enroll in")
                for r in to_enroll:
                    subprocess.run([sys.executable, "enroller.py", r["href"]])
                    logging.info(f'Enrolled into {r["title"], r["day"]}')

                    try:
                        with open(ENROLL_FILE) as f:
                            requests = json.load(f)
                        requests = [x for x in requests if x != r]
                        with open(ENROLL_FILE, "w") as f:
                            json.dump(requests, f, indent=2)
                    except Exception as e:
                        logging.error(f"Error updating enroll_requests.json: {e}")

                    try:
                        try:
                            with open("enroll_log.json") as f:
                                log = json.load(f)
                        except (FileNotFoundError, ValueError):
                            log = []
                        log.append({**r, "enrolled_at": datetime.datetime.now().isoformat()})
                        with open("enroll_log.json", "w") as f:
                            json.dump(log, f, indent=2)
                    except Exception as e:
                        logging.error(f"Error updating enroll_log.json: {e}")
            else:
                logging.info("No classes to enroll in the next 48 hours")
        else:
            logging.info("Scheduler disabled, sleeping...")

        to_unenroll = get_unenroll_requests()
        if to_unenroll:
            logging.info(f"Found {len(to_unenroll)} unenroll requests")
            for r in to_unenroll:
                date = r["start"][:10]
                result = subprocess.run([sys.executable, "unenroller.py", r["title"], date])
                if result.returncode == 0:
                    try:
                        with open("unenroll_requests.json") as f:
                            queue = json.load(f)
                        queue = [x for x in queue if not (x["title"] == r["title"] and x["start"] == r["start"])]
                        with open("unenroll_requests.json", "w") as f:
                            json.dump(queue, f, indent=2)
                    except Exception as e:
                        logging.error(f"Error updating unenroll_requests.json: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
