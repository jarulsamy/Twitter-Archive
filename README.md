# Twitter-Bookmark-Downloader

A CLI python application to download all media (and hopefully more) from all
bookmarked tweets. Eventually I hope to make this a general archive utility for
Twitter, allowing users to download/archive all kinds of tweets.

Originally, before the V2 Twitter API, this app used Selenium to try and scrape
the contents of the a users bookmarks page. Now, since the release of the V2
API, the application has been rewritten. This new version is much faster and
more robust.

## Run

This software is only compatible with **Python 3.9+**.

>TODO: Document how to create Twitter Developer App.

1. Clone the repository

   ```sh
   $ git clone https://github.com/jarulsamy/twitter-bookmark-downloader
   $ cd twitter-bookmark-downloader
   ```

2. Install the application with `setuptools`.

   ```sh
   $ python setup.py install
   ```

3. Run the application

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

The Twitter dev team did an excellent job on the new APIs. The new APIs are
substantially more intuitive and allow us to interact with many more features of
Twitter. While it did take two years, I appreciate the openness, transparency,
and attention to feedback.

The relevant forumn post is available [here](https://twittercommunity.com/t/build-with-bookmarks-on-the-twitter-api-v2/168804).
