"""Core internals of the application.

Contains the major interactions with external APIs.
Handles authentication with Twitter, and fetching all necessary Tweets.
"""
import datetime
import http.server
import json
import os
import socketserver
import time
from json import JSONEncoder
from pathlib import Path
from socket import socket
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

import requests
import tweepy
from tqdm import tqdm


class OneShotTCPServer(socketserver.TCPServer):
    """TCP server to handle a single HTTP request."""

    def serve_forever(self) -> None:
        """Remove unsupported method from parent server.

        :raises: NotImplementedError
        """
        raise NotImplementedError(
            "Use socketserver.TCPServer to handle several requests instead."
        )

    def process_request(self, request: socket, client_address: str) -> Any:
        """Process a single HTTP request to the server.

        :param request: Request from a client to handle.
        :param client_address: Address of the client sending the request.
        :returns: Instance of the request handler.
        """
        handler_inst = self.finish_request(request, client_address)
        self.shutdown_request(request)
        return handler_inst

    def finish_request(self, request: socket, client_address: str) -> Any:
        """Handoff a single request to the handler.

        :param request: Request from a client to handle.
        :param client_address: Address of the client sending the request.
        :returns: Instance of the request handler.
        """
        return self.RequestHandlerClass(request, client_address, self)

    def _handle_request_noblock(self) -> Any:
        try:
            request, client_address = self.get_request()
        except OSError:
            return

        if self.verify_request(request, client_address):
            try:
                # Almost the same as the standard library implementation,
                # but returns an instance of the request handler.
                return self.process_request(request, client_address)
            except Exception:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
        else:
            self.shutdown_request(request)


class OAuthRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handle a OAuth success request."""

    success_resp = r"""<!doctype html>
<html lang="en">
<h1>
Success, you may close this tab!
</h1>
</html>
    """.encode()

    def __init__(self, request: socket, client_address: str, server: str):
        """Initialze a new instance of the handler.

        :param request: Request to handle.
        :param client_address: Address of the client sending the request.
        :param server: Address of the server itself.
        """
        self._token = None
        super().__init__(request, client_address, server)

    def do_GET(self) -> None:
        """Handle a GET request.

        Sends back the OAuth token as a parameter in the URL.
        """
        # Normalize the URL.
        host, port = self.client_address
        self._token = urlunparse(urlparse(f"https://{host}:{port}{self.path}"))

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write(self.success_resp)

    @property
    def token(self) -> str:
        """Retrieve the token.

        :returns: Token assuming successful authentication.
        """
        return self._token


class TweetEncoder(JSONEncoder):
    """Custom encoder to serialize a series of Tweets."""

    def default(self, obj: Any) -> dict:
        """Serialize Tweets, handling recursive cases.

        :param obj: Object to be serialized
        :returns: Ready to be written as JSON, dict equivalent of obj.
        """
        if isinstance(obj, datetime.datetime):
            return str(obj.isoformat())
        elif isinstance(obj, tweepy.ReferencedTweet):
            return obj.data
        else:
            return super().default(obj)


def _oauth(
    save_path: Path,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    use_dotenv: bool = False,
    headless: bool = False,
) -> dict:
    """Authenticate with the Twitter API using OAuth 2.X.

    The client ID and secret parameters, if not specified, are loaded from the
    'TWITTER_ARCHIVE_CLIENT_ID' and 'TWITTER_ARCHIVE_CLIENT_SECRET' environment
    variables respectively.

    :param save_path: Path to save the access token.
    :param client_id: Client ID from the Twitter dev app portal.
    :param client_secret: Client secret from the Twitter dev app portal.
    :param use_dotenv: Load a .env file automatically.
    :param headless: Disable interactive authentication.

    :returns: Access token details.

    :raises: ValueError - Missing client ID: client ID not specified and
                          'TWITTER_ARCHIVE_CLIENT_ID' is unset.
    :raises: ValueError - Missing client secret: client secret not specified and
                          'TWITTER_ARCHIVE_CLIENT_ID' is unset.
    """
    REDIRECT_PORT = 8080
    REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"
    if use_dotenv:
        from dotenv import load_dotenv

        load_dotenv()

    client_id = client_id or os.environ.get("TWITTER_ARCHIVE_CLIENT_ID")
    client_secret = client_secret or os.environ.get("TWITTER_ARCHIVE_CLIENT_SECRET")

    print(client_id)
    print(client_secret)

    if client_id is None:
        raise ValueError("Missing client ID")
    if client_secret is None:
        raise ValueError("Missing client secret")

    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=client_id,
        redirect_uri=REDIRECT_URI,
        scope=["tweet.read", "users.read", "bookmark.read"],
        client_secret=client_secret,
    )
    print(oauth2_user_handler.get_authorization_url())

    if not headless:
        # Start the HTTP server to receive the token.
        handler = OAuthRequestHandler
        with OneShotTCPServer(("", REDIRECT_PORT), handler) as httpd:
            handler_inst = httpd.handle_request()
            response_url = handler_inst.token
    else:
        response_url = input("Enter the response url here: ")

    access_token = oauth2_user_handler.fetch_token(response_url)
    with open(save_path, "w") as fp:
        json.dump(access_token, fp)

    return access_token


def auth(
    cache_path: str = "access_token.json",
    use_cache: bool = True,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    use_dotenv: bool = False,
    headless: bool = False,
) -> tweepy.Client:
    """Login to the Twitter API.

    A wrapper of the _oauth() method, but uses a cache to avoid reauthenticating
    if possible.

    The client ID and secret parameters, if not specified, are loaded from the
    'TWITTER_ARCHIVE_CLIENT_ID' and 'TWITTER_ARCHIVE_CLIENT_SECRET' environment
    variables respectively.

    :param cache_path: Path to cache access token details.
    :param use_cache: Whether to attempt loading token details from cache.
    :param client_id: Client ID from the Twitter dev app portal.
    :param client_secret: Client secret from the Twitter dev app portal.
    :param use_dotenv: Load a .env file automatically.
    :param headless: Disable interactive authentication.

    :returns: Instance of the tweepy client.

    :raises: ValueError: Missing client ID, client ID not specified and
                         'TWITTER_ARCHIVE_CLIENT_ID' is unset.
    :raises: ValueError: Missing client secret, client secret not specified and
                         'TWITTER_ARCHIVE_CLIENT_ID' is unset.
    """
    cache_path = None if cache_path is None else Path(cache_path)
    if not use_cache or not cache_path.is_file():
        access_token = _oauth(
            cache_path,
            client_id=client_id,
            client_secret=client_secret,
            use_dotenv=use_dotenv,
            headless=headless,
        )
    else:
        # Try to use the cache if possible.
        with open(cache_path, "r") as json_file:
            access_token = json.load(json_file)

        # Check if expired, if so re-auth.
        if float(access_token["expires_at"]) < time.time():
            access_token = _oauth(
                cache_path,
                client_id=client_id,
                client_secret=client_secret,
                use_dotenv=use_dotenv,
                headless=headless,
            )

    client = tweepy.Client(
        access_token["access_token"],
        wait_on_rate_limit=True,
    )

    return client


def get_bookmarks(client: tweepy.Client, save_path: Optional[Path] = None) -> dict:
    """Fetch all bookmarked tweets.

    :param client: Authenticated Twitter user whos bookmarks to fetch.
    :param save_path: Path to save manifest of all the tweets.

    :returns: Serialized dict of all the tweets.
    """
    media = {}
    tweets = []

    page_token = None
    while True:
        resp = client.get_bookmarks(
            expansions=[
                "attachments.poll_ids",
                "attachments.media_keys",
                "author_id",
                "geo.place_id",
                "referenced_tweets.id",
            ],
            max_results=100,
            pagination_token=page_token,
            media_fields=[
                "media_key",
                "type",
                "url",
                "duration_ms",
                "height",
                "width",
                "alt_text",
                "variants",
            ],
            place_fields=[
                "full_name",
                "id",
                "geo",
            ],
            poll_fields=[
                "id",
                "options",
                "duration_minutes",
                "end_datetime",
                "voting_status",
            ],
            tweet_fields=[
                "id",
                "text",
                "attachments",
                "author_id",
                "conversation_id",
                "created_at",
                "geo",
                "lang",
                "possibly_sensitive",
                "referenced_tweets",
                "source",
            ],
            user_fields=["id"],
        )

        try:
            for i in resp.includes["media"]:
                media[i.media_key] = i
        except KeyError:
            pass

        for i in resp.data:
            if i.data.get("attachments", {}).get("media_keys") is None:
                tweets.append(dict(i))
                continue

            tweet = dict(i)
            tweet["media"] = []
            for media_key in i["attachments"]["media_keys"]:
                tweet["media"].append(media[media_key].data)

            tweets.append(tweet)

        # We retrieve tweets in pages of 100.
        # Go until no more exist.
        try:
            page_token = resp.meta["next_token"]
        except KeyError:
            break

    data = json.dumps(tweets, indent=2, cls=TweetEncoder)

    if save_path is not None:
        with open(save_path, "w") as fp:
            fp.write(data)

    return json.loads(data)


def download_tweet(
    tweet_obj: dict,
    base_dir: Path,
    clobber: bool = True,
    disable_progress_bar: bool = True,
    chunk_size: int = 1024,
) -> None:
    """Download media from a single tweet.

    :param tweet_obj: Dict including all the attributes of the tweet.
    :param base_dir: Base directory to save any media.
    :param clobber: Overwrite existing files.
    :param disable_progress_bar: Silence the progress bar.
    :param chunk_size: Chunk size to use while downloading content.
    """
    if "id" not in tweet_obj:
        raise AttributeError("Missing attribute ID, is this a valid tweet object?")

    my_dir = base_dir / str(tweet_obj["id"])
    my_dir.mkdir(exist_ok=True)

    try:
        for media in tweet_obj["media"]:
            type_ = media["type"]
            if type_ == "video":
                # Only save videos with a bitrate
                variants = [x for x in media["variants"] if "bit_rate" in x]
                max_variant = max(variants, key=lambda x: x["bit_rate"])
                url = max_variant["url"]
            elif type_ == "photo":
                url = media["url"]
            else:
                raise NotImplementedError(f"Type: '{type_}' not supported")

            dest = my_dir / Path(urlparse(url).path).name
            if dest.exists() and not clobber:
                # TODO Use the logging module
                print(f"'{dest}' already exists. Skipping.")
                continue

            resp = requests.get(url, stream=True)
            length = resp.headers.get("content-length")
            with open(dest, "wb") as f:
                # No content length header
                if length is None:
                    f.write(resp.content)
                else:
                    # Progress bar
                    length = int(length)
                    num_bars = int(length / chunk_size)

                    for chunk in tqdm(
                        resp.iter_content(chunk_size=chunk_size),
                        ascii=True,
                        disable=disable_progress_bar,
                        total=num_bars,
                        desc=dest.name,
                        leave=True,
                        unit="KB",
                        miniters=1,
                        ncols=80,
                    ):
                        f.write(chunk)
    except KeyError:
        return
    except NotImplementedError as e:
        print(e)
        return
