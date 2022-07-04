from TwitterArchive.core import HTTPRequestHandler
import io
import unittest
from urllib.parse import urlparse, urlunparse


class HTTPRequestHandlerTestCase(unittest.TestCase):

    def test_handler(self):
        host = "127.0.0.1"
        port = 8080
        token = "/foo/bar/123?foo"
        expected = f"https://{host}:{port}{token}"

        class MockRequest:
            def makefile(self, *args, **kwargs):
                return io.BytesIO(f"GET {token}".encode())

            def sendall(self, payload):
                return payload

        class MockServer:
            def __init__(server_self, ip_port, Handler):
                handler = Handler(MockRequest(), ip_port, server_self)
                self.assertEqual(expected, handler.token)

        MockServer((host, port), HTTPRequestHandler)
