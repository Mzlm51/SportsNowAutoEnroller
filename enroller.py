from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os, logging, datetime
import sys

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

def login(driver, wait, email, password):
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

def enroll_class(href):
    wait, driver = init_driver()
    driver.get("https://www.sportsnow.ch/users/sign_in")  
    login(driver, wait, EMAIL, PASSWORD)
    logging.info("Successfully Logged In")
    try:
        logging.info(f"Enrolling into {href}")
        driver.get(href)

        #driver.get(driver.find_element(By.XPATH, "//div[@class='col-xs-12 col-md-6 col-sm-6 col-lg-4']/a").get_attribute("href"))
        driver.get(driver.find_element(By.XPATH, "//a[contains(text(), 'Jetzt buchen')]").get_attribute("href"))
        logging.info("section 1 complete")

        # Wait for page to load, then check state before navigating
        wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(@class, 'footable-last-column')]")))

        # Check if already booked
        already_booked = driver.find_elements(By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), 'Bereits gebucht')]")
        if already_booked:
            logging.info("Already booked — skipping.")
            return

        # Check if full (waitlist available)
        waitlist = driver.find_elements(By.XPATH, "//a[contains(@class, 'add-to-waiting-list')]")
        if waitlist:
            driver.get(waitlist[0].get_attribute("href"))
            logging.info("Class full — added to waitlist.")
            return

        driver.get(driver.find_element(By.XPATH, "//a[contains(@class, 'btn-sm') and contains(@class, 'btn-primary') and contains(@class, 'btn-block')]").get_attribute("href"))
        logging.info("section 2 complete")

        auswaehlen = wait.until(
            EC.presence_of_element_located((By.XPATH,
                "//a[contains(@class, 'btn-primary') and contains(text(), 'Auswählen') and not(@data-confirm)]"
            ))
        )
        driver.get(auswaehlen.get_attribute("href"))
        logging.info("section 3 complete")

        verbindlich_buchen = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn btn-primary')]"))
        )

        driver.execute_script("arguments[0].scrollIntoView();", verbindlich_buchen)
        driver.execute_script("arguments[0].click();", verbindlich_buchen)

        import time
        time.sleep(3)

        logging.info("Enrolled in the course!")
        logging.info("Enrollment done!")
    except Exception as e:
        logging.error(f"Error enrolling: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    href = sys.argv[1]
    enroll_class(href)
