"""
Usage: twitter-archive [-o FILE] [--headless] [-h] [-v] [-m FILE | -i FILE]

A CLI Tool to archive tweets

Options:
  -o FILE, --media-output FILE
                        Path to output downloaded media. (default: media)
  --headless            Don't use interactive authentication. (default:
                        False)
  -h, --help            Show this help message ane exit.
  -v, --version         show program's version number and exit
  -m FILE, --manifest-output FILE
                        Path to output bookmark manifest. (default: bookmark-
                        manifest.json)
  -i FILE, --manifest-input FILE
                        Use an existing manifest and download all media.
                        (default: None)
"""

import json
import sys
from multiprocessing.pool import ThreadPool
from pathlib import Path
import argparse

from . import __version__
from .core import auth, download_tweet, get_bookmarks


class CapitalisedHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = "Usage: "
        return super(CapitalisedHelpFormatter, self).add_usage(
            usage,
            actions,
            groups,
            prefix,
        )


def build_parser(exit_on_error=True):
    parser = argparse.ArgumentParser(
        add_help=False,
        description="A CLI Tool to archive tweets",
        formatter_class=CapitalisedHelpFormatter,
        exit_on_error=exit_on_error,
    )

    # Set some more sane capitalization
    parser._positionals.title = "Positional Arguments"
    parser._optionals.title = "Options"

    parser.add_argument(
        "-o",
        "--media-output",
        metavar="FILE",
        action="store",
        type=Path,
        default=Path("./media"),
        help="Path to output downloaded media.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Don't use interactive authentication.",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message ane exit.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    manifest_group = parser.add_mutually_exclusive_group()
    manifest_group.add_argument(
        "-m",
        "--manifest-output",
        action="store",
        metavar="FILE",
        type=Path,
        default=Path("./bookmark-manifest.json"),
        help="Path to output bookmark manifest.",
    )
    manifest_group.add_argument(
        "-i",
        "--manifest-input",
        action="store",
        metavar="FILE",
        type=Path,
        help="Use an existing manifest and download all media.",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args = vars(args)

    client = auth(headless=args["headless"], use_dotenv=True)
    if args["manifest_input"] is not None:
        with open(args["manifest_input"], "r") as fp:
            tweets = json.load(fp)
    else:
        tweets = get_bookmarks(client, save_path=args["manifest_output"])

    base_dir = Path(args["media_output"])
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
