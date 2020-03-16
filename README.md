# Twitter-Bookmark-Downloader

A selenium based python script to download all images from bookmarked tweets.

### Setup

This software is only compatible with **Python 3.6+**.

Install the required dependencies using the `requirements.txt` file.

    pip install -r requirements.txt

> **Selenium** is required for this application when running with python. Please install selenium and the **Firefox Gecko Webdriver**. Add it to your platform specific PATH based on the [Selenium Documentation](https://selenium-python.readthedocs.io/index.html).

### Run

Run `main.py` to start. Enter your username, password, and if enabled, 2fa code when prompted.

Optionally, use the command line arguments:

    usage: main.py [-h][-d DOWNLOAD_DIR] [-u USERNAME][-p PASSWORD] [--headless]

    optional arguments:
      -h, --help            show this help message and exit
      -d DOWNLOAD_DIR, --download_dir DOWNLOAD_DIR
                            Output folder of downloads
      -u USERNAME, --username USERNAME
                            Specify user as argument to circumvent prompt
      -p PASSWORD, --password PASSWORD
                            Specify password as argument
      --headless            Run without user input and firefox window display.

## Support

Reach out to me at one of the following places!

-   Email (Best) at joshua.gf.arul@gmail.com
-   Twitter at <a href="http://twitter.com/jarulsamy_" target="_blank">`@jarulsamy_`</a>

* * *
