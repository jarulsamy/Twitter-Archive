from setuptools import find_packages
from setuptools import setup
from TwitterArchive import __version__


install_requires = [
    "tweepy >= 4.10.0",
    "python-dotenv >= 0.20.0",
]


setup(
    name="twitter-archive",
    version=__version__,
    description="A Suite of Twitter Archival Tools",
    url="https://github.com/jarulsamy/twitter-bookmark-downloader",
    install_requires=install_requires,
    python_requires=">=3.9",
    entry_points={"console_scripts": ["twitter-archive=TwitterArchive.cli:main"]},
)
