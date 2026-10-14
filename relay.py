#!/usr/bin/python3
# The relay (SPEC.md F12 and F4; the first slices of the "gatekeeper"). It
# sits between the chat page and the model server, and every request for the
# model passes through it. It does two jobs:
#
#   1. Usage records. One row per chat request: when, who, which model, how
#      many tokens, how long, how it ended, and how many of the reply's
#      tokens were the model's thinking (to see whether the thinking cap is
#      reached; counted from the length of the thinking, never stored).
#   2. Reserving the server. While the owner has reserved it, new chat
#      requests from anyone else are refused with a clear message. A reply
#      already in progress finishes. The owner's own requests go through.
#      The reservation is off at every start. It is switched from this Mac
#      (llm-reserve), or by the owner from the badge in the chat page.
#
# It never records what anyone typed or what the model replied. Requests and
# replies pass through memory only, as they must to be forwarded.
#
# It listens on this Mac only and uses only what comes with Python. It does
# not depend on which chat page or model server is in use: it expects an
# OpenAI-style API behind it and reads the user from request headers.
#
# One deliberate change to requests: for a streamed chat reply it asks the
# model server to include token counts at the end (stream_options
# include_usage), because servers only report them when asked.
#
# Usage: relay.py LISTEN-PORT MODEL-SERVER-PORT PATH-TO-USAGE-FILE [OWNER-CHECK-ADDRESS]
#
# OWNER-CHECK-ADDRESS is where the chat page's own server answers "who is
# signed in with this token?". Without it, reserving from the badge is off.

import csv
import http.client
import json
import os
import signal
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

if len(sys.argv) not in (4, 5):
    sys.exit("Usage: relay.py LISTEN-PORT MODEL-SERVER-PORT PATH-TO-USAGE-FILE [OWNER-CHECK-ADDRESS]")
LISTEN_PORT = int(sys.argv[1])
UPSTREAM_PORT = int(sys.argv[2])
USAGE_FILE = sys.argv[3]
OWNER_CHECK_ADDRESS = sys.argv[4] if len(sys.argv) == 5 else None

# Headers the chat page attaches to say who sent the request, and the role
# that marks the owner. Change these if the chat page is ever replaced.
USER_NAME_HEADER = "X-OpenWebUI-User-Name"
USER_ID_HEADER = "X-OpenWebUI-User-Id"
USER_ROLE_HEADER = "X-OpenWebUI-User-Role"
OWNER_ROLE = "admin"

# What a guest is told while the server is reserved.
RESERVED_MESSAGE = "The owner is using the server right now. Please try again later."

# Requests whose address ends with one of these are chat requests: they are
# recorded, counted as "in use", and refused while the server is reserved.
RECORDED = ("/chat/completions", "/completions")

# The relay's own addresses. The chat page's server cannot reach them: it
# only ever calls addresses under /v1.
#   status         read-only; also passed to other devices, for the badge.
#   reserve        for the llm-reserve command. Reachable from this Mac only,
#                  so it asks for no proof.
#   owner-reserve  for the badge's switch. Passed to other devices, so every
#                  request must prove it comes from a signed-in owner.
STATUS_ADDRESS = "/relay/status"
RESERVE_ADDRESS = "/relay/reserve"
OWNER_RESERVE_ADDRESS = "/relay/owner-reserve"
# A request to owner-reserve must carry this header. A web page on another
# site cannot add it, which stops such a page from flipping the switch.
SWITCH_HEADER = "X-LLM-Reserve"

# Headers that describe one connection and must not be copied to the other.
NOT_COPIED = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length", "host",
    # Dropped so replies arrive uncompressed and the token counts can be read.
    "accept-encoding",
}

ENDINGS = {"stop": "finished", "length": "length cap"}

file_lock = threading.Lock()

# The relay's state. Kept in memory only, so a restart clears a reservation.
state_lock = threading.Lock()
reserved = False
in_progress = 0

COLUMNS = ["time", "user_name", "user_id", "model", "prompt_tokens",
           "reply_tokens", "seconds", "ended", "thinking_tokens"]


def open_usage_file():
    # Create the file with its heading row if it is not there yet. Only this
    # Mac account may read it.
    if not os.path.exists(USAGE_FILE) or os.path.getsize(USAGE_FILE) == 0:
        with open(USAGE_FILE, "a", newline="") as f:
            csv.writer(f).writerow(COLUMNS)
    else:
        # A file from before a column was added: extend its heading row so
        # the new column has a name. Older rows simply leave it empty.
        with open(USAGE_FILE, newline="") as f:
            lines = f.read().split("\n", 1)
        heading = next(csv.reader([lines[0]]))
        if heading != COLUMNS and COLUMNS[:len(heading)] == heading:
            temporary = USAGE_FILE + ".new"
            with open(temporary, "w", newline="") as f:
                csv.writer(f).writerow(COLUMNS)
                f.write(lines[1] if len(lines) > 1 else "")
            os.replace(temporary, USAGE_FILE)
    os.chmod(USAGE_FILE, 0o600)


def safe(value):
    # A name is chosen by the person who signed up. Stop a spreadsheet from
    # treating one that starts like a formula as a formula.
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return "" if value is None else value


def thinking_tokens(seen):
    # How many of the reply's tokens were thinking. The model server's own
    # count if it gives one; otherwise an estimate: the reply's exact token
    # count, shared out by how many characters were thinking and how many
    # were answer (a reply that hit the thinking cap at 8,000 came out at
    # 7,999). Empty when the reply's token count is unknown.
    if seen["thinking_exact"] is not None:
        return seen["thinking_exact"]
    reply, thinking = seen["reply"], seen["thinking_chars"]
    if not isinstance(reply, int):
        return ""
    total = thinking + seen["answer_chars"]
    return round(reply * thinking / total) if total else 0


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

    def send_json(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response_only(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def row(self, started, model, seen):
        return (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(started)),
            unquote(self.headers.get(USER_NAME_HEADER) or "unknown"),
            self.headers.get(USER_ID_HEADER) or "unknown",
            model if isinstance(model, str) else "unknown",
            seen["prompt"], seen["reply"],
            round(time.time() - started, 1),
            seen["ended"] or "unknown",
            thinking_tokens(seen),
        )

    def note(self, obj, seen):
        # Pick the token counts and the ending out of a reply, and measure how
        # long its thinking and its answer are, in characters. Nothing else
        # in the reply is kept; the text itself is never stored.
        usage = obj.get("usage")
        if isinstance(usage, dict):
            seen["prompt"] = usage.get("prompt_tokens", seen["prompt"])
            seen["reply"] = usage.get("completion_tokens", seen["reply"])
            details = usage.get("completion_tokens_details")
            if isinstance(details, dict) and isinstance(details.get("reasoning_tokens"), int):
                seen["thinking_exact"] = details["reasoning_tokens"]
        for choice in obj.get("choices") or []:
            if not isinstance(choice, dict):
                continue
            if choice.get("finish_reason"):
                seen["ended"] = ENDINGS.get(choice["finish_reason"], choice["finish_reason"])
            # "delta" in a streamed reply, "message" in a whole one.
            part = choice.get("delta") or choice.get("message")
            if isinstance(part, dict):
                thinking = part.get("reasoning_content") or part.get("reasoning")
                if isinstance(thinking, str):
                    seen["thinking_chars"] += len(thinking)
                if isinstance(part.get("content"), str):
                    seen["answer_chars"] += len(part["content"])
                for call in part.get("tool_calls") or []:
                    arguments = (call.get("function") or {}).get("arguments") if isinstance(call, dict) else None
                    if isinstance(arguments, str):
                        seen["answer_chars"] += len(arguments)

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

    def is_owner_signed_in(self):
        # Ask the chat page's server who the sign-in token belongs to. The
        # token is passed on for this one question and is not kept or logged.
        token = self.headers.get("Authorization") or ""
        if not OWNER_CHECK_ADDRESS or not token.startswith("Bearer ") or not self.headers.get(SWITCH_HEADER):
            return False
        try:
            ask = urllib.request.Request(OWNER_CHECK_ADDRESS, headers={"Authorization": token})
            with urllib.request.urlopen(ask, timeout=5) as answer:
                return json.loads(answer.read(65536)).get("role") == OWNER_ROLE
        except (OSError, ValueError, AttributeError):
            return False

    def control(self, path):
        # Asking for the state, or reserving and releasing.
        global reserved
        if int(self.headers.get("Content-Length") or 0) > 1024 or self.headers.get("Transfer-Encoding"):
            self.close_connection = True
            self.send_json(413, {"error": {"message": "Too large."}})
            return
        body = self.read_body()
        if path == OWNER_RESERVE_ADDRESS and self.command == "POST":
            if not self.is_owner_signed_in():
                self.send_json(403, {"error": {"message": "Only the owner can reserve the server."}})
                return
            path = RESERVE_ADDRESS
        if path == RESERVE_ADDRESS and self.command == "POST":
            try:
                want = json.loads(body or b"{}").get("on")
            except (ValueError, AttributeError):
                want = None
            if not isinstance(want, bool):
                self.send_json(400, {"error": {"message": 'Send {"on": true} or {"on": false}.'}})
                return
            with state_lock:
                reserved = want
        elif not (path == STATUS_ADDRESS and self.command == "GET"):
            self.send_json(404, {"error": {"message": "Unknown relay address."}})
            return
        with state_lock:
            is_reserved, count = reserved, in_progress
        self.send_json(200, {
            "state": "reserved" if is_reserved else ("in use" if count else "free"),
            "reserved": is_reserved,
            "requests_in_progress": count,
        })

    def relay(self):
        global in_progress
        path = self.path.split("?")[0]
        if path.startswith("/relay/"):
            self.control(path)
            return

        started = time.time()
        body = self.read_body()
        recorded = self.command == "POST" and path.endswith(RECORDED)
        model = None
        seen = {"prompt": None, "reply": None, "ended": None,
                "thinking_chars": 0, "answer_chars": 0, "thinking_exact": None}

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

            # Reserved: only the owner's requests go on to the model. The
            # check and the count change together, so the state stays right.
            is_owner = (self.headers.get(USER_ROLE_HEADER) or "").lower() == OWNER_ROLE
            with state_lock:
                refused = reserved and not is_owner
                if not refused:
                    in_progress += 1
            if refused:
                seen["ended"] = "refused: reserved"
                self.send_json(503, {"error": {
                    "message": RESERVED_MESSAGE, "type": "server_reserved", "code": "server_reserved"}})
                record(self.row(started, model, seen))
                return

        headers = {k: v for k, v in self.headers.items() if k.lower() not in NOT_COPIED}
        upstream = http.client.HTTPConnection("127.0.0.1", UPSTREAM_PORT)
        try:
            try:
                upstream.request(self.command, self.path, body=body or None, headers=headers)
                reply = upstream.getresponse()
            except (OSError, http.client.HTTPException):
                seen["ended"] = "model server not running"
                self.send_json(502, {"error": {"message": "The model server is not running."}})
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
                with state_lock:
                    in_progress -= 1
                record(self.row(started, model, seen))

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
