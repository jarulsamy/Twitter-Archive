"""Twitter Archival Tool

A CLI tool to archive tweets.

Usage:
    twitter-archive [options]

Options:
    -s, --skip                  Use the existing metadata file if possible.
    -o, --media-output=FILE     Path to output media    [default: ./media]
    -m, --metadata-output=FILE  Path to output metadata [default: ./bookmarks.json]
    --headless                  Don't use interactive authentication

    -h --help                   Show this help
    -v --version                Show version
"""

import json
import sys
from multiprocessing.pool import ThreadPool
from pathlib import Path

from docopt import docopt

from . import __version__
from .core import auth, download_tweet, get_bookmarks


def main():
    args = docopt(__doc__, version=__version__)
    client = auth(headless=args["--headless"], use_dotenv=True)
    if args["--skip"]:
        with open("bookmarks.json", "r") as fp:
            tweets = json.load(fp)
    else:
        tweets = get_bookmarks(client, save_path=args["--metadata-output"])

    base_dir = Path(args["--media-output"])
    base_dir.mkdir(exist_ok=True, parents=True)

    pool = ThreadPool(5)
    try:
        for i, tweet in enumerate(tweets, 1):
            pool.apply_async(download_tweet, args=(tweet, base_dir, 1024, i % 10))

        pool.close()
        pool.join()
    except KeyboardInterrupt:
        pool.terminate()
        pool.join()

    sys.stdout.flush()
    sys.stderr.flush()
