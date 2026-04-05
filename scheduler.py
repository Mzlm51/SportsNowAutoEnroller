import json, datetime, subprocess, time, logging
import sys

logging.basicConfig(level=logging.INFO)

ENROLL_FILE = "enroll_requests.json"
CHECK_INTERVAL = 5  # every minute
HOURS_AHEAD = 48

SCRAPE_HOUR = 18 # when to scrape new batch of classes
SCRAPE_MINUTE = 42
last_scrape_date = None


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
            class_start = class_start.replace(tzinfo=None)
        if now <= class_start <= cutoff:
            to_enroll.append(r)
    return to_enroll

def should_run_daily_scrape():
    global last_scrape_date
    now = datetime.datetime.now()

    if (
        now.hour == SCRAPE_HOUR and
        now.minute == SCRAPE_MINUTE and
        last_scrape_date != now.date()
    ):
            last_scrape_date = now.date()
            return True

    return False


def main():
    global last_scrape_date

    while True:
        now = datetime.datetime.now()

        if should_run_daily_scrape() and autoscrape_enabled():
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

                    #remove request from json after enrolling
                    try:
                        with open(ENROLL_FILE) as f:
                            requests = json.load(f)
                        requests = [x for x in requests if x != r]
                        with open(ENROLL_FILE, "w") as f:
                            json.dump(requests, f, indent=2)
                    except Exception as e:
                        logging.error(f"Error updating enroll_requests.json: {e}")
            else:
                logging.info("No classes to enroll in the next 48 hours")
        else:
            logging.info("Scheduler disabled, sleeping...")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
