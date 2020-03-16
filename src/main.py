import argparse
from getpass import getpass
from pathlib import Path

from bookmarker import TwitterBookmarkDownloader

ap = argparse.ArgumentParser()
ap.add_argument(
    "-d",
    "--download_dir",
    required=False,
    help="Output folder of downloads",
    default=Path(Path.home(), "Downloads", "twitter_downloader"),
)

ap.add_argument(
    "-u",
    "--username",
    required=False,
    help="Specify user as argument to circumvent prompt, must use -p",
)

ap.add_argument("-p", "--password", required=False, help="Specify password as argument")

ap.add_argument(
    "--headless",
    required=False,
    action="store_true",
    help="Run without user input and firefox window display.",
)
args = vars(ap.parse_args())

if not args["headless"]:
    if args["username"] is None:
        args["username"] = input("Username: ")
    if args["password"] is None:
        args["password"] = getpass("Password: ")


downloader = TwitterBookmarkDownloader(
    username=args["username"],
    password=args["password"],
    download_dir=args["download_dir"],
    headless=args["headless"],
)

downloader.login()
downloader.get_bookmarks()
