"""
Main entrypoint to the program from CLI.

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

import argparse
import itertools
import json
from multiprocessing.pool import ThreadPool
from pathlib import Path

from . import __version__
from .core import auth, download_tweet, get_bookmarks


class CapitalisedHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Use a more sane capitaliztion in help argparse help menus."""

    def add_usage(self, usage, actions, groups, prefix=None):
        """Usage formatter."""
        if prefix is None:
            prefix = "Usage: "
        return super(CapitalisedHelpFormatter, self).add_usage(
            usage,
            actions,
            groups,
            prefix,
        )


def _nat_int(s):
    int_val = int(s)
    if int_val < 1:
        raise argparse.ArgumentTypeError("Cannot be less than 1")
    return int_val


# TODO: Add dry run
# TODO: Add quiet
def build_parser(exit_on_error=True):
    """Build the CLI parser.

    :param exit_on_error: Terminate the program (sys.exit) if there is a
                          semantic failure with CLI flags.
    """
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
        "--no-clobber",
        action="store_true",
        help="Don't redownload/overwrite existing media.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable download progress bars",
    )
    parser.add_argument(
        "--num-download-threads",
        metavar="N",
        type=_nat_int,
        default=8,
        help="Number of threads to use while downloading media.",
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
    """Entrypoint from CLI.

    Parse the CLI arguments, and download all the tweets.
    """
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

    num_download_threads = args["num_download_threads"]
    if num_download_threads == 1:
        for tweet in tweets:
            download_tweet(tweet, base_dir, not args["no_clobber"], args["quiet"])
    else:
        pool = ThreadPool(num_download_threads)
        payloads = zip(
            tweets,
            itertools.repeat(base_dir),
            itertools.repeat(not args["no_clobber"]),
            itertools.repeat(args["quiet"]),
        )
        pool.starmap(download_tweet, payloads)
