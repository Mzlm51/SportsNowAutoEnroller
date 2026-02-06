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
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    driver.maximize_window()
    return wait, driver

def login(driver, wait, email, password):
    logging.info("Logging in...")
    input_mail = driver.find_element(By.NAME, "user[email]")
    input_password = driver.find_element(By.NAME, "user[password]")

    input_mail.send_keys(EMAIL)
    input_password.send_keys(PASSWORD)

    login_button = driver.find_element(By.NAME, "commit")
    login_button.click()
    logging.info("Finished logging in")

def enroll_class(href):
    wait, driver = init_driver()
    driver.get("https://www.sportsnow.ch/users/sign_in")  
    login(driver, wait, EMAIL, PASSWORD)
    logging.info("Successfully Logged In")
    try:
        logging.info(f"Enrolling into {href}")
        driver.get(href)

        driver.get(driver.find_element(By.XPATH, "//div[@class='col-xs-12 col-md-6 col-sm-6 col-lg-4']/a").get_attribute("href"))

        driver.get(driver.find_element(By.XPATH, "//a[contains(@class, 'btn btn-primary btn-sm btn-block') and not(contains(text(), 'Anmeldung Geschlossen'))]").get_attribute("href"))

        driver.get(driver.find_element(By.XPATH, "//a[contains(@class, 'btn btn-primary') and not(@data-confirm)]").get_attribute("href"))

        verbindlich_buchen = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn btn-primary')]"))
        )

        driver.execute_script("arguments[0].scrollIntoView();", verbindlich_buchen)

        verbindlich_buchen.click()

        logging.info("Enrolled in the course!")
        logging.info("Enrollment done!")
    except Exception as e:
        logging.error(f"Error enrolling: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    href = sys.argv[1]
    enroll_class(href)
