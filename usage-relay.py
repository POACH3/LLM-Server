#!/usr/bin/python3
# The usage relay (SPEC.md F12). Sits between the chat page and the model
# server, passes every request through, and records one row per chat request:
# when, who, which model, how many tokens, how long, and how it ended.
#
# It never records what anyone typed or what the model replied. Requests and
# replies pass through memory only, as they must to be forwarded.
#
# It listens on this Mac only and uses only what comes with Python. It does
# not depend on which chat page or model server is in use: it expects an
# OpenAI-style API behind it and reads the user from two request headers.
#
# One deliberate change to requests: for a streamed chat reply it asks the
# model server to include token counts at the end (stream_options
# include_usage), because servers only report them when asked.
#
# Usage: usage-relay.py LISTEN-PORT MODEL-SERVER-PORT PATH-TO-USAGE-FILE

import csv
import http.client
import json
import os
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

if len(sys.argv) != 4:
    sys.exit("Usage: usage-relay.py LISTEN-PORT MODEL-SERVER-PORT PATH-TO-USAGE-FILE")
LISTEN_PORT = int(sys.argv[1])
UPSTREAM_PORT = int(sys.argv[2])
USAGE_FILE = sys.argv[3]

# Headers the chat page attaches to say who sent the request. Change these
# two names if the chat page is ever replaced.
USER_NAME_HEADER = "X-OpenWebUI-User-Name"
USER_ID_HEADER = "X-OpenWebUI-User-Id"

# Requests whose address ends with one of these are recorded.
RECORDED = ("/chat/completions", "/completions")

# Headers that describe one connection and must not be copied to the other.
NOT_COPIED = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length", "host",
    # Dropped so replies arrive uncompressed and the token counts can be read.
    "accept-encoding",
}

ENDINGS = {"stop": "finished", "length": "length cap"}

file_lock = threading.Lock()

COLUMNS = ["time", "user_name", "user_id", "model", "prompt_tokens",
           "reply_tokens", "seconds", "ended"]


def open_usage_file():
    # Create the file with its heading row if it is not there yet. Only this
    # Mac account may read it.
    if not os.path.exists(USAGE_FILE) or os.path.getsize(USAGE_FILE) == 0:
        with open(USAGE_FILE, "a", newline="") as f:
            csv.writer(f).writerow(COLUMNS)
    os.chmod(USAGE_FILE, 0o600)


def safe(value):
    # A name is chosen by the person who signed up. Stop a spreadsheet from
    # treating one that starts like a formula as a formula.
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return "" if value is None else value


def record(row):
    try:
        with file_lock:
            with open(USAGE_FILE, "a", newline="") as f:
                csv.writer(f).writerow([safe(v) for v in row])
    except OSError as e:
        print("Could not record a usage row: %s" % e, file=sys.stderr, flush=True)


class Relay(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def read_body(self):
        if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
            parts = []
            while True:
                size = int(self.rfile.readline().split(b";")[0].strip() or b"0", 16)
                if size == 0:
                    while self.rfile.readline().strip():
                        pass
                    return b"".join(parts)
                parts.append(self.rfile.read(size))
                self.rfile.readline()
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def note(self, obj, seen):
        # Pick the token counts and the ending out of a reply. Nothing else
        # in the reply is kept.
        usage = obj.get("usage")
        if isinstance(usage, dict):
            seen["prompt"] = usage.get("prompt_tokens", seen["prompt"])
            seen["reply"] = usage.get("completion_tokens", seen["reply"])
        for choice in obj.get("choices") or []:
            if isinstance(choice, dict) and choice.get("finish_reason"):
                seen["ended"] = ENDINGS.get(choice["finish_reason"], choice["finish_reason"])

    def note_stream_line(self, line, seen):
        line = line.strip()
        if not line.startswith(b"data:"):
            return
        data = line[5:].strip()
        if not data.startswith(b"{"):
            return
        try:
            self.note(json.loads(data), seen)
        except ValueError:
            pass

    def refuse(self):
        body = json.dumps({"error": {"message": "The model server is not running."}}).encode()
        self.send_response_only(502)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def relay(self):
        started = time.time()
        body = self.read_body()
        recorded = self.command == "POST" and self.path.split("?")[0].endswith(RECORDED)
        model = None
        seen = {"prompt": None, "reply": None, "ended": None}

        if recorded:
            try:
                request = json.loads(body)
                model = request.get("model")
                if request.get("stream"):
                    options = request.get("stream_options") or {}
                    if not options.get("include_usage"):
                        options["include_usage"] = True
                        request["stream_options"] = options
                        body = json.dumps(request).encode()
                del request
            except (ValueError, AttributeError):
                pass

        headers = {k: v for k, v in self.headers.items() if k.lower() not in NOT_COPIED}
        upstream = http.client.HTTPConnection("127.0.0.1", UPSTREAM_PORT)
        try:
            try:
                upstream.request(self.command, self.path, body=body or None, headers=headers)
                reply = upstream.getresponse()
            except (OSError, http.client.HTTPException):
                seen["ended"] = "model server not running"
                self.refuse()
                return

            self.send_response_only(reply.status, reply.reason)
            for name, value in reply.getheaders():
                if name.lower() not in NOT_COPIED:
                    self.send_header(name, value)

            if "text/event-stream" in (reply.getheader("Content-Type") or ""):
                # A streamed reply: pass each piece on the moment it arrives.
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                rest = b""
                while True:
                    try:
                        piece = reply.read1(65536)
                    except (OSError, http.client.HTTPException):
                        seen["ended"] = seen["ended"] or "error"
                        break
                    if not piece:
                        break
                    try:
                        self.wfile.write(piece)
                    except OSError:
                        # The person pressed Stop or closed the page.
                        seen["ended"] = "stopped"
                        break
                    if recorded:
                        *lines, rest = (rest + piece).split(b"\n")
                        for line in lines:
                            self.note_stream_line(line, seen)
            else:
                no_body = self.command == "HEAD" or reply.status in (204, 304)
                data = b"" if no_body else reply.read()
                if not no_body:
                    self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                if recorded:
                    try:
                        self.note(json.loads(data), seen)
                    except (ValueError, AttributeError):
                        pass
                    if reply.status >= 400:
                        seen["ended"] = "error %d" % reply.status
        finally:
            upstream.close()
            if recorded:
                record((
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(started)),
                    unquote(self.headers.get(USER_NAME_HEADER) or "unknown"),
                    self.headers.get(USER_ID_HEADER) or "unknown",
                    model if isinstance(model, str) else "unknown",
                    seen["prompt"], seen["reply"],
                    round(time.time() - started, 1),
                    seen["ended"] or "unknown",
                ))

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = relay

    def log_message(self, format, *args):
        # Keep no record of requests other than the usage rows.
        pass


def stop(signum, frame):
    sys.exit(0)


# Set these explicitly: a program started in the background by a script
# otherwise ignores the interrupt signal that llm-stop sends.
signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

open_usage_file()
server = ThreadingHTTPServer(("127.0.0.1", LISTEN_PORT), Relay)
server.daemon_threads = True
server.serve_forever()
