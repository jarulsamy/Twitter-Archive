from getpass import getpass
from pathlib import Path

from bookmarker import TwitterBookmarkDownloader


download_dir = Path(Path.home(), "Downloads", "twitter_downloader")

username = input("Username: ")
password = getpass("Password: ")

downloader = TwitterBookmarkDownloader(
    username=username, password=password, download_dir=download_dir, headless=False,
)

downloader.login()
downloader.get_bookmarks()
