"""Twitter Archival Tool

A CLI tool to archive tweets.

Usage:
    twitter-archive [options]

Options:
    --headless         Don't use interactive authentication
    -o, --output=FILE  Path to output metadata [default: ./bookmarks.json]

    -h --help          Show this help
    -v --version       Show version
"""

from docopt import docopt

from . import __version__

from .core import auth, download_tweet_metadata

try:
    import dotenv

    use_dotenv = True
except ImportError:
    use_dotenv = False


def main():
    args = docopt(__doc__, version=__version__)
    client = auth(headless=args["--headless"], use_dotenv=use_dotenv)
    download_tweet_metadata(client, save_path=args["--output"])

    # TODO: Download all the media
