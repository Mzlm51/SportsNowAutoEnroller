from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os, logging, sys, json

load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

logging.basicConfig(level=logging.INFO)

def init_driver():
    import platform
    from selenium.webdriver.chrome.service import Service
    options = webdriver.ChromeOptions()
    if platform.system() != "Windows":
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-zygote")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1920,1080")
        options.binary_location = "/usr/bin/chromium"
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    return wait, driver

def login(driver, wait):
    logging.info("Logging in...")
    try:
        driver.execute_script("""
            var el = document.querySelector('.cc-window');
            if (el) el.style.display = 'none';
        """)
    except Exception:
        pass
    input_mail = wait.until(EC.presence_of_element_located((By.NAME, "user[email]")))
    input_password = driver.find_element(By.NAME, "user[password]")
    input_mail.send_keys(EMAIL)
    input_password.send_keys(PASSWORD)
    login_button = driver.find_element(By.NAME, "commit")
    driver.execute_script("arguments[0].click();", login_button)
    logging.info("Finished logging in")

def unenroll_class(title, date):
    parts = date.split("-")
    date_display = f"{parts[2]}.{parts[1]}.{parts[0]}"

    wait, driver = init_driver()
    try:
        driver.get("https://www.sportsnow.ch/users/sign_in")
        login(driver, wait)

        wait.until(EC.presence_of_element_located((By.XPATH, "//a[@title='Meine Stunden']")))
        driver.get("https://www.sportsnow.ch/de/bookings")

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "footable-even")))

        rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'footable')]")
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_text = " ".join(c.text for c in cells)
                if title in row_text and date_display in row_text:
                    stornieren = row.find_element(By.XPATH, ".//a[contains(text(), 'Stornieren')]")
                    stornieren.click()
                    wait.until(EC.alert_is_present())
                    driver.switch_to.alert.accept()
                    logging.info(f"Unenrolled from {title} on {date}")
                    try:
                        with open("enroll_log.json") as f:
                            log = json.load(f)
                        log = [e for e in log if not (e["title"] == title and e["start"][:10] == date)]
                        with open("enroll_log.json", "w") as f:
                            json.dump(log, f, indent=2)
                    except Exception:
                        pass
                    return True
            except Exception as row_err:
                logging.error(f"Row error: {row_err}")
                continue
        logging.error(f"Could not find booking for {title} on {date_display}")
        return False
    except Exception as e:
        logging.error(f"Error unenrolling: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    title = sys.argv[1]
    date = sys.argv[2]
    unenroll_class(title, date)
