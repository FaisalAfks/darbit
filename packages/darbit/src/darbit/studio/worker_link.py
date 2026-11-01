"""darbit Studio's line to the input worker (worker.py): requests and their replies, and the worker's events.

The worker is started when the first recording starts and kept for the Studio's life; one that died is started
again on the next request. Tests hand in two streams instead of a process.
"""

import subprocess
import sys
import threading
from collections.abc import Callable
from typing import BinaryIO

from ..service.protocol import Event, ProtocolError, Reply, Request, decode, encode

REPLY_WAIT = 15.0  # seconds for the worker's answer (saving a long recording takes a moment)


class WorkerGone(RuntimeError):
    """The worker didn't answer: it ended, or never started."""


class WorkerLink:
    """Requests to the input worker, and its events to `on_event(topic, data)`."""

    def __init__(self, on_event: Callable[[str, dict], None], streams: tuple[BinaryIO, BinaryIO] | None = None):
        self.on_event = on_event
        self.streams = streams  # (from the worker, to the worker); None: start the worker as a process
        self.process: subprocess.Popen | None = None
        self.reader: BinaryIO | None = None
        self.writer: BinaryIO | None = None
        self.lock = threading.Lock()
        self.next_id = 1
        self.waiting: dict[int, list] = {}  # request id -> [done event, reply]

    def call(self, method: str, **params: object) -> object:
        """The worker's answer; ValueError with its reason when it refuses, WorkerGone when it can't."""
        self._open()
        with self.lock:
            request_id = self.next_id
            self.next_id += 1
            slot: list = [threading.Event(), None]
            self.waiting[request_id] = slot
            try:
                self.writer.write(encode(Request(request_id, method, dict(params))))
                self.writer.flush()
            except (OSError, ValueError) as error:
                self.waiting.pop(request_id, None)
                self._lost()
                raise WorkerGone("the input worker ended") from error
        if not slot[0].wait(REPLY_WAIT):
            raise WorkerGone(f"the input worker didn't answer {method}")
        reply = slot[1]
        if reply is None:
            raise WorkerGone("the input worker ended")
        if reply.error:
            raise ValueError(reply.error)
        return reply.result

    def close(self) -> None:
        if self.writer is not None:
            try:
                self.writer.close()  # the worker ends when its stdin does
            except OSError:
                pass
        if self.process is not None:
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
        self.writer = None

    def _open(self) -> None:
        if self.writer is not None and (self.process is None or self.process.poll() is None):
            return
        if self.streams is not None:
            self.reader, self.writer = self.streams
        else:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            self.process = subprocess.Popen(
                [sys.executable, "-m", "darbit.worker"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                creationflags=flags,
            )
            self.reader, self.writer = self.process.stdout, self.process.stdin
        threading.Thread(target=self._read, args=(self.reader,), name="darbit-worker-link", daemon=True).start()

    def _read(self, reader: BinaryIO) -> None:
        try:
            for line in reader:
                try:
                    message = decode(line)
                except ProtocolError:
                    continue
                if isinstance(message, Reply):
                    with self.lock:
                        slot = self.waiting.pop(message.id, None)
                    if slot is not None:
                        slot[1] = message
                        slot[0].set()
                elif isinstance(message, Event):
                    self.on_event(message.topic, message.data)
        except (OSError, ValueError):
            pass
        self._lost()

    def _lost(self) -> None:
        """The worker ended: wake everyone waiting, and start it again next time."""
        with self.lock:
            left = list(self.waiting.values())
            self.waiting.clear()
            if self.streams is None:
                self.writer = None
        for slot in left:
            slot[0].set()
