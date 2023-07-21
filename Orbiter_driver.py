import random
import pandas as pd
import colorlog
import requests
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import sys
import os
import json



if not os.path.isfile('config_user.json'):

    print("You need to set parameter, they can be change any time in 'config_user' file")
    min_delay = input("Enter the minimum delay between actions: ")
    max_delay = input("Enter the maximum delay between actions: ")
    lower_percentage = float(input("Please enter the min percentage bar (without the % sign): "))
    upper_percentage = float(input("Please enter the max percentage bar (without the % sign): "))
    metamask_identificator = input("Enter metamask Identificator: ")
    min_percentage = lower_percentage / 100
    max_percentage = upper_percentage / 100

    config_user = {
        'min_delay': min_delay,
        'max_delay': max_delay,
        'min_percentage': min_percentage,
        'max_percentage': max_percentage,
        'metamask_identificator': metamask_identificator,
    }

    with open('config_user.json', 'w') as f:
        json.dump(config_user, f)

    print("Configuration saved successfully.")
else:
    print("Configuration file already exists, it can be change any time in 'config_user' file")


with open('config_user.json', 'r') as f:
    config_user = json.load(f)


min_delay = float(config_user['min_delay'])
max_delay = float(config_user['max_delay'])
min_percentage = float(config_user['min_percentage'])
max_percentage = float(config_user['max_percentage'])
metamask_identificator = (config_user['metamask_identificator'])



metamask_url = f"chrome-extension://{metamask_identificator}/home.html#"
data_path = "Data.xlsx"


data = pd.read_excel(data_path, engine='openpyxl', dtype={"Profile ID": str, "Password": str})

start_idx = int(input("Enter the starting index of the profile range: ")) - 1
end_idx = int(input("Enter the ending index of the profile range: ")) - 1
print("For the purpose of avoiding detection, your selected range of profiles was shuffled.")

indices = list(range(start_idx, end_idx + 1))  # Convert the range to a list
random.shuffle(indices)  # Shuffle the list
def confirm_transaction(driver, logger):

    metamask_window_handle = find_metamask_notification(driver, logger)

    if metamask_window_handle:
        find_confirm_button_js = '''
        function findConfirmButton() {
          return document.querySelector('[data-testid="page-container-footer-next"]');
        }
        return findConfirmButton();
        '''
        confirm_button = driver.execute_script(find_confirm_button_js)

        if confirm_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", confirm_button)
            for i in range(5):
                if metamask_window_handle not in driver.window_handles:
                    logger.info("Action is approve")
                    return True
                logger.info(f"Click attempt {i + 1}")
                driver.execute_script("arguments[0].click();", confirm_button)
                time.sleep(3)
            logger.info("Action is approve")
            return True
        else:
            logger.warning("Confirm button not found")
            return False
    else:
        logger.warning(f"MetaMask Notification window not found after 5 attempts")
        return False
def setup_logger(logger_name):
    logger = colorlog.getLogger(logger_name)

    # Removes previous handlers, if they exist.
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "|%(log_color)s%(asctime)s| - Profile [%(name)s] - %(levelname)s - %(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
def click_if_exists(driver, locator):
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            element = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, locator))
            )
            element.click()
            time.sleep(random.uniform(1.3, 2.1))
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(3)
    return False
def find_metamask_notification(driver, logger):
    metamask_window_handle = None

    for attempt in range(5):
        time.sleep(5)

        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            if 'MetaMask Notification' in driver.title:
                metamask_window_handle = handle
                logger.info("MetaMask window found!")
                break

        if metamask_window_handle:
            break

    return metamask_window_handle
def input_text_if_exists(driver, locator, text):
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, locator))
            )
            # Clearing the input field
            element.clear()
            # Write the new text into the field
            for character in text:
                element.send_keys(character)
                time.sleep(random.uniform(0.075, 0.124))
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(3)
    return False
def connect_to_orbiter(driver, logger):

    driver.get('https://www.orbiter.finance/')
    try:
        connected = WebDriverWait(driver, 7).until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app"]/div[1]/div[1]/div[2]/div[1]/span')))
        logger.info("Look like you connected to Orbiter before, great...")
    except TimeoutException:
        click_if_exists(driver, "/html/body/div[1]/div[1]/div[1]/div[2]/span")
        click_if_exists(driver, "/html/body/div[1]/div[2]/div/div[2]/span")

        find_metamask_notification(driver, logger)
        metamask_window_handle = find_metamask_notification(driver, logger)
        if metamask_window_handle:
            click_if_exists(driver, "/html/body/div[1]/div/div[2]/div/div[3]/div[2]/button[2]")
            click_if_exists(driver, "/html/body/div[1]/div/div[2]/div/div[2]/div[2]/div[2]/footer/button[2]")
            driver.switch_to.window(driver.window_handles[0])
        else:
            logger.info("No window found")
def process_profile(idx):

    profile_id = data.loc[idx, "Profile ID"]
    password = data.loc[idx, "Password"]

    logger = setup_logger(f'{idx + 1}')

    open_url = f"http://local.adspower.net:50325/api/v1/browser/start?user_id={profile_id}"
    resp = requests.get(open_url).json()

    if resp["code"] != 0:
        print(resp["msg"])
        print("Failed to start a driver")
        sys.exit()

    chrome_driver = resp["data"]["webdriver"]
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", resp["data"]["ws"]["selenium"])
    driver = webdriver.Chrome(service=Service(chrome_driver), options=chrome_options)
    initial_window_handle = driver.current_window_handle
    time.sleep(1.337)
    for tab in driver.window_handles:
        if tab != initial_window_handle:
            driver.switch_to.window(tab)
            logger.info("Cleaning tabs...")
            driver.close()

    driver.switch_to.window(initial_window_handle)

    driver.get(metamask_url)
    password_input = '//*[@id="password"]'
    input_text_if_exists(driver, password_input, password)
    connection_confirm = '//*[@id="app-content"]/div/div[3]/div/div/button'
    click_if_exists(driver, connection_confirm)

    logger.info("Check annoying button")
    try:
        element = WebDriverWait(driver, 7).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="popover-content"]/div/div/section/div[2]/div/div[2]/div/button'))
        )
        element.click()
        logger.info("Found")
    except TimeoutException:
        math = 1+6

    selector = '/html/body/div[1]/div/div[1]/div/div[2]/div/div'

    click_if_exists(driver, selector)
    click_if_exists(driver, "//*[contains(text(), 'Optimism')]")
    Optimism_value = driver.find_element(By.XPATH,
        '/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div/span[2]')
    value1 = float(Optimism_value.text)

    click_if_exists(driver, selector)
    click_if_exists(driver, "//*[contains(text(), 'Arbitrum One')]")
    Arbitrum_value = driver.find_element(By.XPATH,
        '/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div[1]/div/div/div/div[1]/div/span[2]')
    value2 = float(Arbitrum_value.text)

    greatest_value = max(value1, value2)


    if greatest_value == value1:

        logger.info("Look like you have more token on Optimism...")
        click_if_exists(driver, selector)
        click_if_exists(driver, "//*[contains(text(), 'Optimism')]")

        connect_to_orbiter(driver, logger)
        driver.get("https://www.orbiter.finance/?source=Optimism&dest=zkSync%20Era")
        mu = (random.uniform(min_percentage, max_percentage))
        format_value1 = format(value1 * mu, '.5f')
        input_text_if_exists(driver, "/html/body/div/div[1]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/input",
                             str(format_value1))

        logger.info("Give 30 sec for Orbiter to load element")
        time.sleep(30)
        button_xpath = "/html/body/div[1]/div[1]/div[2]/div/div[2]/div/span"
        button_element = driver.find_element(By.XPATH, button_xpath)
        driver.execute_script("arguments[0].click();", button_element)

        click_if_exists(driver, "/html/body/div[1]/div[1]/div[2]/div/div[4]/div/span")
        confirm_transaction(driver, logger)
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(5)
        logger.info("Done!")
        driver.close()

    elif greatest_value == value2:

        logger.info("Look like you have more token on Arbitrum...")

        click_if_exists(driver, selector)
        click_if_exists(driver, "//*[contains(text(), 'Arbitrum One')]")

        connect_to_orbiter(driver, logger)
        driver.get("https://www.orbiter.finance/?source=Arbitrum&dest=zkSync%20Era")
        mu = (random.uniform(min_percentage, max_percentage))
        format_value2 = format(value2 * mu, '.5f')
        input_text_if_exists(driver, "/html/body/div/div[1]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/input",
                              str(format_value2))

        logger.info("Give 30 sec for Orbiter to load element")
        time.sleep(30)
        button_xpath = "/html/body/div[1]/div[1]/div[2]/div/div[2]/div/span"
        button_element = driver.find_element(By.XPATH, button_xpath)
        driver.execute_script("arguments[0].click();", button_element)

        click_if_exists(driver, "/html/body/div[1]/div[1]/div[2]/div/div[4]/div/span")
        confirm_transaction(driver, logger)
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(5)
        logger.info("Done!")
        driver.close()

        sleep = round(random.uniform(min_delay, max_delay))
        logger.info(f"Wait {sleep} before next swap")
        time.sleep(sleep)


logger_junior = setup_logger("THREAD LOGING")

with ThreadPoolExecutor(max_workers=1) as executor:  # Adjust max_workers as needed
    # Submit tasks to executor
    futures = {}
    for idx in indices:
        futures[executor.submit(process_profile, idx)] = idx

    # Collect results as they become available
    for future in concurrent.futures.as_completed(futures):
        idx = futures[future]
        future.result()