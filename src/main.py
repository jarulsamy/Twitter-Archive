import tweepy
from dotenv import load_dotenv
import os
from pprint import pprint
import json
from json import JSONEncoder
from pathlib import Path
import time
import datetime


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

REDIRECT_URI = "https://localhost:8080"


# print(API_KEY)
# print(API_KEY_SECRET)
# print(BEARER_TOKEN)
# print(ACCESS_TOKEN)
# print(ACCESS_TOKEN_SECRET)
# print(CLIENT_ID)
# print(CLIENT_SECRET)


def auth():
    oauth2_user_handler = tweepy.OAuth2UserHandler(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=["tweet.read", "users.read", "bookmark.read"],
        client_secret=CLIENT_SECRET,
    )

    print(oauth2_user_handler.get_authorization_url())
    reponse_url = input("Enter the response url here: ")
    access_token = oauth2_user_handler.fetch_token(reponse_url)

    with open(CACHE_PATH, "w") as json_file:
        json.dump(access_token, json_file)

    return access_token


if not CACHE_PATH.is_file():
    access_token = auth()
else:
    with open(CACHE_PATH, "r") as json_file:
        access_token = json.load(json_file)

    if float(access_token["expires_at"]) < time.time():
        print("Cache expired, reauth")
        access_token = auth()


print(access_token)

client = tweepy.Client(
    access_token["access_token"],
)
resps = []
media = {}
tweets = []

page_token = None
while True:
    resp = client.get_bookmarks(
        expansions=[
            "author_id",
            "referenced_tweets.id",
            "attachments.media_keys",
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
        tweet_fields=[
            "author_id",
            "created_at",
        ],
    )
    try:
        page_token = resp.meta["next_token"]
    except KeyError:
        break

    resps.append(resp)

    try:
        for i in resp.includes["media"]:
            media[i.media_key] = i
    except KeyError:
        pass

    for i in resp.data:
        if (
            i.get("attachments") is None
            or i.get("attachments").get("media_keys") is None
        ):
            tweets.append(dict(i))
            continue


        tweet = dict(i)

        tweet["media"] = []
        for media_key in i["attachments"]["media_keys"]:
            tweet["media"].append(media[media_key].data)

        tweets.append(tweet)

    # pprint(media)

pprint(tweets)
with open("bookmarks.json", "w") as fp:
    json.dump(tweets, fp, indent=2, cls=TweetEncoder)
