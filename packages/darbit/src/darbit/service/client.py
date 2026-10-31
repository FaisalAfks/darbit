"""Talking to darbit's service from Python: the CLI and the Studio use this.

    with Client("darbit cli") as service:
        service.call("bot.start", bot="ad-bot")
        service.on_event(print)        # (topic, data) for everything that happens from now on

`ensure_running()` starts the service in the background first if it isn't already.
"""

import json
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Self

from .host import address_file
from .protocol import HOST, Event, Hello, ProtocolError, Reply, Request, decode, encode

CONNECT_WAIT = 2.0  # seconds to connect to a service that's there
REPLY_WAIT = 60.0  # seconds for an answer (stopping a bot can take 10)
START_WAIT = 10.0  # seconds for a service started in the background to answer


class ServiceError(RuntimeError):
    """The service refused a request, or couldn't be reached."""


class NotRunning(ServiceError):
    """No service is answering."""


class _Waiting:
    def __init__(self) -> None:
        self.done = threading.Event()
        self.reply: Reply | None = None


class Client:
    """One connection to the service."""

    def __init__(self, name: str = "darbit", address: Path | None = None) -> None:
        port, token = _read_address(address or address_file())
        try:
            self.socket = socket.create_connection((HOST, port), timeout=CONNECT_WAIT)
        except OSError as error:
            raise NotRunning("darbit's service isn't running: start it with darbit serve") from error
        self.socket.settimeout(None)
        self.file = self.socket.makefile("rwb")
        self.lock = threading.Lock()
        self.next_id = 1
        self.waiting: dict[int, _Waiting] = {}
        self.listeners: list[Callable[[str, dict], None]] = []
        self._send(Hello(token, name))
        greeting = decode(self.file.readline() or b"{}")
        if not isinstance(greeting, Reply) or greeting.error:
            self.close()
            raise ServiceError(getattr(greeting, "error", None) or "the service didn't answer hello")
        threading.Thread(target=self._read, name="darbit-service-client", daemon=True).start()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def call(self, method: str, **params: object) -> object:
        """Ask the service; its result, or ServiceError with its reason."""
        with self.lock:
            request_id = self.next_id
            self.next_id += 1
            waiting = _Waiting()
            self.waiting[request_id] = waiting
        self._send(Request(request_id, method, dict(params)))
        if not waiting.done.wait(REPLY_WAIT):
            raise ServiceError(f"no answer to {method} in {REPLY_WAIT:.0f} s")
        reply = waiting.reply
        if reply is None:
            raise NotRunning("the service went away")
        if reply.error:
            raise ServiceError(reply.error)
        return reply.result

    def on_event(self, listener: Callable[[str, dict], None]) -> None:
        """Call `listener(topic, data)` for every event from now on (on the client's reading thread)."""
        self.listeners.append(listener)

    def close(self) -> None:
        try:
            self.socket.close()
        except OSError:
            pass

    def _send(self, message: Hello | Request) -> None:
        try:
            with self.lock:
                self.file.write(encode(message))
                self.file.flush()
        except OSError as error:
            raise NotRunning("the service went away") from error

    def _read(self) -> None:
        try:
            for line in self.file:
                try:
                    message = decode(line)
                except ProtocolError:
                    continue
                if isinstance(message, Reply):
                    self._answered(message)
                elif isinstance(message, Event):
                    for listener in list(self.listeners):
                        listener(message.topic, message.data)
        except OSError:
            pass
        with self.lock:
            left = list(self.waiting.values())
            self.waiting.clear()
        for waiting in left:
            waiting.done.set()  # no reply: the service went away

    def _answered(self, reply: Reply) -> None:
        with self.lock:
            waiting = self.waiting.pop(reply.id, None)
        if waiting is not None:
            waiting.reply = reply
            waiting.done.set()


def _read_address(path: Path) -> tuple[int, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data["port"]), str(data["token"])
    except (OSError, ValueError, KeyError) as error:
        raise NotRunning("darbit's service isn't running: start it with darbit serve") from error


def running() -> bool:
    """Whether a service answers."""
    try:
        with Client("darbit check") as service:
            service.call("service.ping")
        return True
    except ServiceError:
        return False


def ensure_running() -> None:
    """Start the service in the background unless one already answers."""
    if running():
        return
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    subprocess.Popen(
        [sys.executable, "-m", "darbit", "serve"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
        start_new_session=sys.platform != "win32",
    )
    deadline = time.monotonic() + START_WAIT
    while time.monotonic() < deadline:
        if running():
            return
        time.sleep(0.1)
    raise NotRunning("darbit's service didn't start: run darbit serve to see why")
