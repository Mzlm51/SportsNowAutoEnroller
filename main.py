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

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

logging.basicConfig(level=logging.INFO, format= '%(asctime)s - %(levelname)s - %(message)s')

service = Service(executable_path="./chromedriver.exe")
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 10)

day_map = {
    1: "Monday", 8: "Monday", 15: "Monday",
    2: "Tuesday", 9: "Tuesday", 16: "Tuesday",
    3: "Wednesday", 10: "Wednesday", 17: "Wednesday",
    4: "Thursday", 11: "Thursday", 18: "Thursday",
    5: "Friday", 12: "Friday", 19: "Friday",
    6: "Saturday", 13: "Saturday", 20: "Saturday",
    7: "Sunday", 14: "Sunday", 21: "Sunday"
}


dayToEnroll = "Monday"
timeToEnroll = "12:00 - 13:15"

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
times = []

def main():
    try:
        driver.maximize_window()
        driver.get("https://www.sportsnow.ch/users/sign_in")  
        enroll_course()
    except Exception as e:
        logging.error  (f"An error occurred: {e}")    
    finally:
        driver.quit()

def enroll_course():

    input_mail = driver.find_element(By.NAME, "user[email]")
    input_password = driver.find_element(By.NAME, "user[password]")

    input_mail.send_keys(EMAIL)
    input_password.send_keys(PASSWORD)

    login_button = driver.find_element(By.NAME, "commit")
    login_button.click()
    logging.info("finished login in")

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, 'Meine Studios')]"))
    ).click()

    logging.info("Clicked 'Meine Studios'")

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='https://www.sportsnow.ch/go/natthapong-gym?locale=de']"))
    ).click()

    logging.info("Clicked Anschauen")

    wait.until(
        EC.element_to_be_clickable((By.XPATH,"//a[text()='Stundenplan']"))
    ).click()
    
    logging.info("Clicked Stundenplan")
    

    # start by scraping the data and creating the time table of the classes
    classes = driver.find_elements(By.XPATH, "//div[contains(@class, 'col-xs-1 cal-entry-col') and contains(@class, 'cal-col-')]/div[contains(@class, 'cal-entry') and not(contains(.,'Probetraining'))]")

    # block : [day, time, href]
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
                    numbers = re.findall('\d+', parent_class)
                    number = int(numbers[1])
                    day = day_map[number]

                    # get time
                    time_element = block.find_element(By.XPATH, ".//p[.//i[contains(@class, 'fa-clock-o')]]")
                    time_text = time_element.text.strip()
                    if time_text not in times:
                        times.append(time_text)


                    # get href
                    href = block.find_element(By.XPATH, ".//a").get_attribute("href")
                    classMap[(day,time_text)] = href


            break # break out of while loop if successful


        except StaleElementReferenceException:
            logging.warning("Retrying")
            driver.refresh
            time.sleep(3)
            retryCount += 1
        except Exception as e:
            logging.error(f"Error {e} occured")
            break

    # print(classMap)
    # print("Times found:", times)

    classToGoTo = classMap.get((dayToEnroll,timeToEnroll))
    # print(classToGoTo)
    logging.info("Got the class")

    driver.get(classToGoTo)
    
    driver.get(driver.find_element(By.XPATH, "//div[@class='col-xs-12 col-md-6 col-sm-6 col-lg-4']/a").get_attribute("href"))

    driver.get(driver.find_element(By.XPATH, "//a[contains(@class, 'btn btn-primary btn-sm btn-block') and not(contains(text(), 'Anmeldung Geschlossen'))]").get_attribute("href"))

    driver.get(driver.find_element(By.XPATH, "//a[contains(@class, 'btn btn-primary') and not(@data-confirm)]").get_attribute("href"))


    verbindlich_buchen = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn btn-primary')]"))
    )

    driver.execute_script("arguments[0].scrollIntoView();", verbindlich_buchen)

    verbindlich_buchen.click()

    logging.info("Enrolled into the Course!")


if __name__ == "__main__":
    main()