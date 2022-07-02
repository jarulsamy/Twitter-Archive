import tweepy
import pickle
from pprint import pprint

import sys

sys.setrecursionlimit(2_000)

print("foo")
with open("data.pickle", "rb") as fp:
    resps = pickle.load(fp)
print("bar")

print(resps)
