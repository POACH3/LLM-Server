#!/usr/bin/python3
# Shows the offline page while the private LLM server is stopped.
#
# Tailscale's Mac app can only pass visitors on to a program listening on a
# port; it cannot show a web page from a file. This small program is that
# listener: it answers every request, whatever the address, with the page in
# offline/index.html.
#
# Started by llm-stop and ended by llm-start. It listens on this Mac only,
# records nothing about who asks, and uses only what comes with Python.
#
# Usage: offline-page.py PORT PATH-TO-PAGE

import signal
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if len(sys.argv) != 3:
    sys.exit("Usage: offline-page.py PORT PATH-TO-PAGE")
PORT = int(sys.argv[1])
PAGE = sys.argv[2]

# Fail at start, not at the first visitor, if the page is missing.
with open(PAGE, "rb"):
    pass


class OfflinePage(BaseHTTPRequestHandler):
    def answer(self):
        # Read the page each time, so an edit shows without a restart.
        with open(PAGE, "rb") as f:
            body = f.read()
        # 503 means "temporarily unavailable". Browsers still show the page,
        # and the page's own script uses it to tell that the chat is not back.
        self.send_response(503)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Retry-After", "30")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_OPTIONS = answer

    def log_message(self, format, *args):
        # Keep no record of requests.
        pass


def stop(signum, frame):
    sys.exit(0)


# Set these explicitly: a program started in the background by a script
# otherwise ignores the interrupt signal that llm-start sends.
signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

server = ThreadingHTTPServer(("127.0.0.1", PORT), OfflinePage)
server.daemon_threads = True
server.serve_forever()
