"""Main entrypoint to the program from CLI."""
import argparse
import itertools
import json
import logging
import shutil
from multiprocessing.pool import ThreadPool
from pathlib import Path

from . import __version__
from .core import auth, download_tweet, get_bookmarks


class CapitalizedHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Use a more sane capitaliztion in help argparse help menus."""

    def __init__(self, prog: str) -> None:
        """Use the terminal width to determine width."""
        width, height = shutil.get_terminal_size((80, None))
        super().__init__(prog, width=width)

    def add_usage(self, usage, actions, groups, prefix=None):
        """Usage formatter."""
        if prefix is None:
            prefix = "Usage: "
        return super(CapitalizedHelpFormatter, self).add_usage(
            usage,
            actions,
            groups,
            prefix,
        )


def nat_int(s: str) -> int:
    """Type validator for natural integers."""
    int_val = int(s)
    if int_val < 1:
        raise argparse.ArgumentTypeError("Cannot be less than 1")
    return int_val


def build_parser(exit_on_error: bool = True) -> argparse.ArgumentParser:
    """Build the CLI parser.

    :param exit_on_error: Terminate the program (sys.exit) if there is a
                          semantic failure with CLI flags.
    """
    parser = argparse.ArgumentParser(
        add_help=False,
        description="A CLI Tool to archive tweets",
        formatter_class=CapitalizedHelpFormatter,
        exit_on_error=exit_on_error,
    )

    # Set some more sane capitalization
    parser._positionals.title = "Positional Arguments"
    parser._optionals.title = "Options"

    parser.add_argument(
        "--client-id",
        action="store",
        metavar="ID",
        help="Specify the client ID.",
    )
    parser.add_argument(
        "--client-secret",
        action="store",
        metavar="ID",
        help="Specify the client ID.",
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
        "--num-download-threads",
        metavar="N",
        type=nat_int,
        default=8,
        help="Number of threads to use while downloading media.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable download progress bars",
    )
    parser.add_argument(
        "-o",
        "--media-output",
        metavar="FILE",
        action="store",
        type=Path,
        default=Path("./media"),
        help="Path to output downloaded media.",
    )

    # Mutually exclusive options.
    manifest_group = parser.add_mutually_exclusive_group()
    manifest_group.add_argument(
        "-i",
        "--manifest-input",
        action="store",
        metavar="FILE",
        type=Path,
        help="Use an existing manifest and download all media.",
    )
    manifest_group.add_argument(
        "-m",
        "--manifest-output",
        action="store",
        metavar="FILE",
        type=Path,
        default=Path("./bookmark-manifest.json"),
        help="Path to output bookmark manifest.",
    )

    # Generic
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message ane exit.",
    )

    return parser


def _setup_logging(lvl: int) -> logging.Logger:
    if lvl == 0:
        log_level = logging.ERROR
    elif lvl == 1:
        log_level = logging.WARNING
    elif lvl == 2:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=logging.ERROR,  # Third party libs use this log level
        format="%(asctime)s %(name)-16s %(levelname)-8s %(threadName)s %(message)s",
    )

    logger = logging.getLogger("twitter-archive")
    # My code uses this log level
    logger.setLevel(log_level)
    logger.debug(
        "Initialized logger with log level %s (verbose=%s)",
        logging._levelToName[log_level],
        lvl,
    )

    return logger


def main() -> None:
    """Entrypoint from CLI.

    Parse the CLI arguments, and download all the tweets.
    """
    parser = build_parser()
    args = parser.parse_args()
    args = vars(args)

    logger = _setup_logging(args["verbose"])

    logger.debug("Authenticating")
    client = auth(
        headless=args["headless"],
        client_id=args["client_id"],
        client_secret=args["client_secret"],
        use_dotenv=True,
    )

    if args["manifest_input"] is not None:
        logger.info("Loaded existing manifest from '%s'", args["manifest_input"])
        with open(args["manifest_input"], "r") as fp:
            tweets = json.load(fp)
    else:
        logger.info("Fetching manifest from Twitter.")
        tweets = get_bookmarks(client, save_path=args["manifest_output"])

    base_dir = Path(args["media_output"])
    base_dir.mkdir(exist_ok=True, parents=True)

    num_download_threads = args["num_download_threads"]
    logger.info("Downloading all media with %d threads", num_download_threads)
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
