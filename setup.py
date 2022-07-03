from setuptools import setup
from TwitterArchive import __version__


install_requires = [
    "python-dotenv >= 0.20.0",
    "requests >= 2.28.1",
    "tqdm >= 4.64.0",
    "tweepy >= 4.10.0",
]


setup(
    name="twitter-archive",
    version=__version__,
    description="A Suite of Twitter Archival Tools",
    url="https://github.com/jarulsamy/twitter-bookmark-downloader",
    packages=["TwitterArchive"],
    install_requires=install_requires,
    python_requires=">=3.9",
    entry_points={"console_scripts": ["twitter-archive=TwitterArchive.cli:main"]},
)
