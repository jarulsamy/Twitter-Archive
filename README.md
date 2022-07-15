<h1 align="center">Twitter-Archive</h1>
<p align="center"
<a href="https://github.com/jarulsamy/Twitter-Archive/actions"><img alt="Action Status" src="https://github.com/jarulsamy/Twitter-Archive/actions/workflows/python-version-test.yml/badge.svg"></a>
<img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/Twitter-Archive">
<a href="https://pypi.org/project/Twitter-Archive/"><img alt="PyPI" src="https://img.shields.io/pypi/v/Twitter-Archive"></a>
<img alt="Total LOC" src="https://img.shields.io/tokei/lines/github/jarulsamy/Twitter-Archive">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

A CLI Python application to download all media (and hopefully more) from
bookmarked tweets (for now). Eventually I hope to make this a general archive
utility for Twitter, allowing users to download/archive all kinds of tweets.

Originally, before the V2 Twitter API, this app used Selenium to try and scrape
the contents of the a users bookmarks page. Now, since the release of the V2
API, the application has been rewritten. This new version is much faster and
more robust.

---

## Installation and Setup

### Installation

_Twitter-Archive_ can be installed with `pip`

    ```sh
    $ pip install twitter-archive
    ```

Alternatively, you can clone this repository and install from the repository
instead of from PyPi.

    ```sh
    $ git clone https://github.com/jarulsamy/Twitter-Archive
    $ cd Twitter-Archive
    $ pip install .
    ```

To properly authenticate with the Twitter API, you will have to create a
developer application. This will provide you with a client ID and client secret.

> TODO: Document how to create Twitter Developer App.

### Usage

You can invoke the app with:

    ```sh
    $ twitter-archive
    ```

By default, the app will print a URL to prompt the user to authorize the
application with Twitters official APIs. Once you navigate to that link and
login with Twitter, the app will fetch a manifest of all the bookmarked tweets
and begin saving any photos/videos to disk.

You can view the built-in CLI help menu for more info:

```txt
$ twitter-archive --help
Twitter Archival Tool

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

```

## Acknowledgements

The Twitter developer team did an excellent job on the new APIs. The new APIs
are substantially more intuitive and allow us to interact with many more
features of Twitter. While it did take two years, the openness, transparency,
and attention to feedback is much appreciated!

The relevant forumn post is available [here](https://twittercommunity.com/t/build-with-bookmarks-on-the-twitter-api-v2/168804).
