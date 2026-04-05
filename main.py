from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from dotenv import load_dotenv
import os
import time
import logging
import re
import datetime
import json

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

day_map = {
    1: "Monday", 8: "Monday", 15: "Monday",
    2: "Tuesday", 9: "Tuesday", 16: "Tuesday",
    3: "Wednesday", 10: "Wednesday", 17: "Wednesday",
    4: "Thursday", 11: "Thursday", 18: "Thursday",
    5: "Friday", 12: "Friday", 19: "Friday",
    6: "Saturday", 13: "Saturday", 20: "Saturday",
    7: "Sunday", 14: "Sunday", 21: "Sunday"
}

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
times = []

def init():
    import platform
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

    # hide cookie banner if present
    try:
        driver.execute_script("""
            var el = document.querySelector('.cc-window');
            if (el) el.style.display = 'none';
        """)
        logging.info("cookie banner hid")
    except Exception:
        pass
    
    input_mail = wait.until(EC.presence_of_element_located((By.NAME, "user[email]")))
    input_password = driver.find_element(By.NAME, "user[password]")

    input_mail.send_keys(email)
    input_password.send_keys(password)

    login_button = driver.find_element(By.NAME, "commit")
    driver.execute_script("arguments[0].click();", login_button)
    logging.info("Finished logging in")

def scrapeWebsite(driver, wait):
    logging.info("Scraping website...")

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, 'Meine Studios')]"))
    ).click()

    logging.info("Clicked 'Meine Studios'")

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='https://www.sportsnow.ch/go/natthapong-gym?locale=de']"))
    ).click()

    logging.info("Clicked Anschauen")

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[text()='Stundenplan']"))
    ).click()

    logging.info("Clicked Stundenplan")

    # start by scraping the data and creating the time table of the classes
    classes = driver.find_elements(By.XPATH, "//div[contains(@class, 'col-xs-1 cal-entry-col') and contains(@class, 'cal-col-')]/div[contains(@class, 'cal-entry') and not(contains(.,'Probetraining'))]")

    classMap = {}

    maxRetries = 3
    retryCount = 0

    while retryCount < maxRetries:
        try:
            classes = driver.find_elements(
                By.XPATH, "//div[contains(@class, 'col-xs-1 cal-entry-col') and contains(@class, 'cal-col-')]/div[contains(@class, 'cal-entry') and not(contains(.,'Probetraining'))]")

            for block in classes:
                # get day
                parent_class = block.find_element(By.XPATH, "..").get_attribute("class")
                numbers = re.findall(r'\d+', parent_class)
                number = int(numbers[1])
                day = day_map[number]

                # get time
                time_element = block.find_element(By.XPATH, ".//p[.//i[contains(@class, 'fa-clock-o')]]")
                time_text = time_element.text.strip()
                if time_text not in times:
                    times.append(time_text)

                # get name
                class_title_element = block.find_element(By.XPATH, ".//h4/a/span")
                class_title = class_title_element.text.strip()

                # get href
                href = block.find_element(By.XPATH, ".//a").get_attribute("href")
                classMap[(day, time_text, class_title)] = href

            break  # break out of while loop if successful

        except StaleElementReferenceException:
            logging.warning("Retrying...")
            driver.refresh()
            time.sleep(3)
            retryCount += 1
        except Exception as e:
            logging.error(f"Error {e} occurred")
            break

    #logging.info(f"Classes found: {classMap}")
    print(classMap)
    return classMap

# block : [day, time, name, href]
def save_to_json(classMap):
    output = []

    today = datetime.date.today()

    for (day, time_range, title), href in classMap.items():
        start_time, end_time = time_range.split(" - ")

        # find next date for this weekday
        weekday_index = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(day)
        days_ahead = (weekday_index - today.weekday()) % 7
        class_date = today + datetime.timedelta(days=days_ahead)

        start_dt = datetime.datetime.strptime(
            f"{class_date} {start_time}", "%Y-%m-%d %H:%M"
        )
        end_dt = datetime.datetime.strptime(
            f"{class_date} {end_time}", "%Y-%m-%d %H:%M"
        )

        output.append({
            "class_title": title,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "href": href,
            "day": day
        })

    with open("classes.json", "w") as f:
        json.dump(output, f, indent=2)

    logging.info("Saved classes to classes.json")

def main():
    wait, driver = init()

    try:
        driver.get("https://www.sportsnow.ch/users/sign_in")  
        login(driver, wait, EMAIL, PASSWORD)
        classMap = scrapeWebsite(driver, wait)
        save_to_json(classMap)
        logging.info("Finished scraping the website")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
