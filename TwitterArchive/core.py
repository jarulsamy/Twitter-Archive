import datetime
import http.server
import json
import os
import socketserver
import time
from json import JSONEncoder
from pathlib import Path
from urllib.parse import urlparse

import requests
import tweepy
from tqdm import tqdm


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


def _oauth(
    save_path,
    client_id=None,
    client_secret=None,
    use_dotenv=False,
    headless=False,
):
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
    cache_path="access_token.json",
    use_cache=True,
    client_id=None,
    client_secret=None,
    use_dotenv=False,
    headless=False,
):
    """Login to the Twitter API"""
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


def get_bookmarks(client, save_path=None):
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


def download_tweet(tweet_obj, base_dir: Path, chunk_size=1024, position=0):
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
                        total=num_bars,
                        desc=dest.name,
                        leave=True,
                        unit="KB",
                        position=position,
                        miniters=1,
                        ncols=80,
                    ):
                        f.write(chunk)
    except KeyError:
        return
    except NotImplementedError as e:
        print(e)
        return
