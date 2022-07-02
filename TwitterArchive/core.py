from dotenv import load_dotenv
from json import JSONEncoder
from pathlib import Path
import datetime
import json
import os
import time
import tweepy

import http.server
import socketserver

# DEBUG
from pprint import pprint


class OneShotTCPServer(socketserver.TCPServer):
    def serve_forever(self) -> None:
        raise NotImplementedError(
            "Use socketserver.TCPServer to handle several requests instead."
        )

    def process_request(self, request, client_address):
        """Call finish_request."""
        handler_inst = self.finish_request(request, client_address)
        self.shutdown_request(request)
        return handler_inst

    def finish_request(self, request, client_address):
        return self.RequestHandlerClass(request, client_address, self)

    def _handle_request_noblock(self):
        """Handle one request, without blocking."""
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


class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    resp = r"""<!doctype html>
<html lang="en">
<h1>
Success, you may close this tab!
</h1>
</html>
    """.encode()

    def __init__(self, *args, **kwargs):
        self._token = None
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self._token = f"https://{self.address_string()}{self.path}"

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write(self.resp)

    @property
    def token(self):
        return self._token


class TweetEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return str(obj.isoformat())
        elif isinstance(obj, tweepy.ReferencedTweet):
            return obj.data
        else:
            return super().default(obj)


load_dotenv()

CACHE_PATH = Path("access_token_cache.json")
API_KEY = os.environ.get("API_KEY", "")
API_KEY_SECRET = os.environ.get("API_KEY_SECRET", "")
BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET", "")
CLIENT_ID = os.environ.get("CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")

REDIRECT_PORT = 8080
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"


def _oauth(save_path, headless=False):
    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=["tweet.read", "users.read", "bookmark.read"],
        client_secret=CLIENT_SECRET,
    )
    print(oauth2_user_handler.get_authorization_url())

    if not headless:
        # Start the HTTP server to receive the token.
        handler = HTTPRequestHandler
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
    cache_path="access_token.json", use_cache=True, headless=False
) -> tweepy.Client:
    """Login to the Twitter API"""
    cache_path = None if cache_path is None else Path(cache_path)
    if not use_cache or not cache_path.is_file():
        access_token = _oauth(cache_path, headless)
    else:
        # Try to use the cache if possible.
        with open(cache_path, "r") as json_file:
            access_token = json.load(json_file)

        # Check if expired, if so re-auth.
        if float(access_token["expires_at"]) < time.time():
            access_token = _oauth(cache_path, headless)

    client = tweepy.Client(
        access_token["access_token"],
        wait_on_rate_limit=True,
    )

    return client


client = auth()

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

with open("bookmarks.json", "w") as fp:
    json.dump(tweets, fp, indent=2, cls=TweetEncoder)
