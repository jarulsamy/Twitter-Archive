import argparse
import contextlib
import io
import unittest
from pathlib import Path

from TwitterArchive.cli import build_parser
from TwitterArchive import __version__


class CLITestCase(unittest.TestCase):
    def test_help_short(self):
        # Setup
        stdout = io.StringIO()

        parser = build_parser(False)
        argv = ["-h"]
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit):
                parser.parse_args(argv)

        self.assertIn("help", stdout.getvalue())

    def test_help_long(self):
        # Setup
        stdout = io.StringIO()

        parser = build_parser(False)
        argv = ["--help"]
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit):
                parser.parse_args(argv)

        self.assertIn("help", stdout.getvalue())

    def test_version_short(self):
        # Setup
        stdout = io.StringIO()

        parser = build_parser(False)
        argv = ["-v"]
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit):
                parser.parse_args(argv)

        self.assertIn(__version__, stdout.getvalue())

    def test_version(self):
        # Setup
        stdout = io.StringIO()

        parser = build_parser(False)
        argv = ["--version"]
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit):
                parser.parse_args(argv)

        self.assertIn(__version__, stdout.getvalue())

    def test_no_args(self):
        parser = build_parser(False)

        argv = []
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": None,
                "manifest_output": Path("bookmark-manifest.json"),
                "media_output": Path("media"),
            },
        )

    def test_media_arg_short(self):
        parser = build_parser(False)

        argv = ["-o", "foobar"]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": None,
                "manifest_output": Path("bookmark-manifest.json"),
                "media_output": Path("foobar"),
            },
        )

    def test_media_arg_long(self):
        parser = build_parser(False)

        argv = ["--media-output", "foobar"]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": None,
                "manifest_output": Path("bookmark-manifest.json"),
                "media_output": Path("foobar"),
            },
        )

    def test_manifest_arg_short(self):
        parser = build_parser(False)

        argv = ["-m", "foobar"]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": None,
                "manifest_output": Path("foobar"),
                "media_output": Path("media"),
            },
        )

    def test_manifest_arg_long(self):
        parser = build_parser(False)

        argv = ["--manifest-output", "foobar"]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": None,
                "manifest_output": Path("foobar"),
                "media_output": Path("media"),
            },
        )

    def test_manifest_input_short(self):
        parser = build_parser(False)

        argv = ["-i", "foobar"]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": Path("foobar"),
                "manifest_output": Path("bookmark-manifest.json"),
                "media_output": Path("media"),
            },
        )

    def test_manifest_input_long(self):
        parser = build_parser(False)

        argv = ["--manifest-input", "foobar"]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": Path("foobar"),
                "manifest_output": Path("bookmark-manifest.json"),
                "media_output": Path("media"),
            },
        )

    def test_headless(self):
        parser = build_parser(False)

        argv = ["--headless"]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": True,
                "manifest_input": None,
                "manifest_output": Path("bookmark-manifest.json"),
                "media_output": Path("media"),
            },
        )

    def test_mutual_exclusion(self):
        parser = build_parser(False)

        argv = ["-m", "manifest-output", "-i", "manifest-input"]
        with self.assertRaises(argparse.ArgumentError):
            parser.parse_args(argv)

    def test_many_short(self):
        parser = build_parser(False)

        argv = ["-o", "media-output", "-m", "manifest-output"]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": None,
                "manifest_output": Path("manifest-output"),
                "media_output": Path("media-output"),
            },
        )

    def test_many_long(self):
        parser = build_parser(False)

        argv = [
            "--media-output",
            "media-output",
            "--manifest-output",
            "manifest-output",
        ]
        args = parser.parse_args(argv)
        args = vars(args)
        self.assertDictEqual(
            args,
            {
                "headless": False,
                "manifest_input": None,
                "manifest_output": Path("manifest-output"),
                "media_output": Path("media-output"),
            },
        )
