<h1 align="center">Twitter-Archive</h1>
<p align="center"
<a href="https://github.com/jarulsamy/Twitter-Archive/actions"><img alt="Action Status" src="https://github.com/jarulsamy/Twitter-Archive/actions/workflows/python-version-test.yml/badge.svg"></a>
<img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/Twitter-Archive">
<a href="https://pypi.org/project/Twitter-Archive/"><img alt="PyPI" src="https://img.shields.io/pypi/v/Twitter-Archive"></a>
<img alt="Total LOC" src="https://img.shields.io/tokei/lines/github/jarulsamy/Twitter-Archive">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/jarulsamy/Twitter-Archive/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/jarulsamy/Twitter-Archive"></a>
</p>

A CLI Python application to download all media (and hopefully more) from
bookmarked tweets (for now). Eventually I hope to make this a general archive
utility for Twitter, allowing users to download/archive all kinds of tweets.

Originally, before the V2 Twitter API, this app used Selenium to try and scrape
the contents of a users bookmarks page. Now, since the release of the V2 API,
the application has been rewritten. This new version is much faster and more
robust.

---

## Installation and Setup

### Installation

_Twitter-Archive_ can be installed with `pip`

    $ pip install twitter-archive

Alternatively, you can clone this repository and install from the repository
instead of from PyPi.

    $ git clone https://github.com/jarulsamy/Twitter-Archive
    $ cd Twitter-Archive
    $ pip install .

To properly authenticate with the Twitter API, you will have to create a
developer application. This will provide you with a client ID and client secret.

> TODO: Document how to create Twitter Developer App.

### Usage

You can invoke the app with:

    $ twitter-archive

By default, the app will print a URL to prompt the user to authorize the
application with Twitters official APIs. Once you navigate to that link and
login with Twitter, the app will fetch a manifest of all the bookmarked tweets
and begin saving any photos/videos to disk.

You can view the built-in CLI help menu for more info:

```txt
$ twitter-archive --help
Usage: twitter-archive [-o FILE] [--headless] [--no-clobber] [--quiet] [--num-download-threads N] [-v] [-h] [--version]
                    [-m FILE | -i FILE]

A CLI Tool to archive tweets

Options:
-o FILE, --media-output FILE
                        Path to output downloaded media. (default: media)
--headless            Don't use interactive authentication. (default: False)
--no-clobber          Don't redownload/overwrite existing media. (default: False)
--quiet               Disable download progress bars (default: False)
--num-download-threads N
                        Number of threads to use while downloading media. (default: 8)
-v, --verbose
-h, --help            Show this help message ane exit.
--version             show program's version number and exit
-m FILE, --manifest-output FILE
                        Path to output bookmark manifest. (default: bookmark-manifest.json)
-i FILE, --manifest-input FILE
                        Use an existing manifest and download all media. (default: None)## Acknowledgements
```

## Acknowledgements

The Twitter developer team did an excellent job on the new APIs. The new APIs
are substantially more intuitive and allow us to interact with many more
features of Twitter. While it did take two years, the openness, transparency,
and attention to feedback is much appreciated!

The relevant forum post is available
[here](https://twittercommunity.com/t/build-with-bookmarks-on-the-twitter-api-v2/168804).
