import os
import re
import time
from pathlib import Path
from urllib.request import urlopen

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()


class TwitterBookmarkDownloader(object):
    def __init__(self, username=None, password=None, download_dir=None, headless=True):
        self.LOGIN_URL = "https://twitter.com/login"
        self.BOOKMARK_URL = "https://twitter.com/i/bookmarks"
        self.username = username
        self.password = password
        self.download_dir = download_dir
        # If not specified, try using env vars.
        if self.username is None:
            self.username = os.getenv("TWITTER_USERNAME")
        if self.password is None:
            self.password = os.getenv("TWITTER_PASSWORD")
        if self.download_dir is None:
            self.download_dir = os.getenv("TWITTER_DOWNLOAD_PATH")

        # Webdriver setup
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=options)

    def __del__(self):
        self.driver.quit()

    def login(self):
        self.driver.get(self.LOGIN_URL)

        # Wait till page is loaded
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "session[username_or_email]"))
            )
        # Timeout of 10 seconds
        except TimeoutException:
            return Exception("Page didn't load")

        uname = self.driver.find_element_by_name("session[username_or_email]")
        pword = self.driver.find_element_by_name("session[password]")
        try:
            uname.send_keys(self.username)
            pword.send_keys(self.password)
        except TypeError:
            raise ValueError("Missing username/password")

        # Find the submit button
        self.driver.find_element_by_xpath(
            "/html/body/div/div/div/div/main/div/div/form/div/div[3]/div/div"
        ).click()

        time.sleep(1)

        if self.driver.current_url == self.LOGIN_URL:
            raise Exception("Authentication Error")
        elif "locked" in self.driver.current_url:
            raise Exception("Account locked")

        authenticated = False
        while not authenticated:
            if "login_verification" in self.driver.current_url:
                auth_code = self.driver.find_element_by_name("challenge_response")
                auth_code.clear()
                code = input("Enter 2fa code: ")
                auth_code.send_keys(code)
                self.driver.find_element_by_id("email_challenge_submit").click()
            else:
                authenticated = True

    def get_bookmarks(self):
        self.driver.get(self.BOOKMARK_URL)
        time.sleep(1)

        time.sleep(1)
        images = self.driver.find_elements_by_tag_name("img")
        urls = [img.get_attribute("src") for img in images]

        if not os.path.isdir(self.download_dir):
            os.mkdir(self.download_dir)

        for url in urls:
            if "media" in url:
                # driver.get(url)
                filename, format_ = os.path.split(url)[1].split("?")
                ext = re.findall("format=\w{3}", format_)[0].split("=")[1]
                img_data = urlopen(url).read()
                path = Path(self.download_dir, f"{filename}.{ext}")
                with open(path, "wb") as f:
                    f.write(img_data)
                print(f"Downloaded file to: {path}")
