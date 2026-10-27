# SportsNow Auto-Enroller

A Python tool that watches the class schedule on [SportsNow.ch](https://sportsnow.ch)
and automatically enrolls me in selected Muay Thai sessions, with a small web interface
to manage requests. Runs unattended on a Raspberry Pi.

> For legal reasons this project is purely educational.

## What it does

- **Scrapes the schedule** from SportsNow.ch and stores class data as structured JSON.
- **Logs in automatically** and enrolls in chosen classes as soon as they open.
- **Unenrolls** from classes on request.
- **Schedules** enrollment and unenrollment runs so bookings happen at the right time
  without manual input.
- **Web interface** (served locally) to add and review enroll/unenroll requests.
- **Persists state and logs** to JSON so runs are traceable across restarts.

## How it works

| File | Role |
| --- | --- |
| `main.py` | Entry point that ties the pieces together |
| `enroller.py` / `unenroller.py` | Enroll and unenroll logic against SportsNow |
| `scheduler.py` | Runs enroll/unenroll jobs at scheduled times |
| `server.py` + `index.html` | Local web interface for managing requests |
| `classes.json` | Available / tracked classes |
| `*_requests.json`, `*_log.json`, `scheduler_status.json` | Runtime state and logs |

## Getting started

```bash
git clone https://github.com/Mzlm51/SportsNowAutoEnroller.git
cd SportsNowAutoEnroller

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Then run the web interface / scheduler:

```bash
python main.py
```

> Add the exact run commands and any flags here once finalised.

## Configuration

Your SportsNow login and any personal settings should be supplied via environment
variables or a local config file that is **not** committed. Keep credentials out of the
repository.

## Deployment

Designed to run continuously on a Raspberry Pi (e.g. as a `systemd` service or a `cron`
job that keeps the scheduler alive), so bookings happen automatically while the Pi is on.

## Notes

- Built as a personal automation project to practise web scraping, login automation,
  scheduling, and a lightweight web UI.
- Educational use only; respect SportsNow's terms of service.
