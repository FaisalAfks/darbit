"""The input worker: recording in a process of its own, so nothing else in darbit can delay an input or lose a count.

darbit Studio starts it (`python -m darbit.worker`) and talks to it over its stdin and stdout with darbit's messages
(service/protocol.py): requests and replies, and `record.tick` events while recording. The work is
server/record_api.py's. Bots play their tapes in their own process, which has nothing else running either.
See the rebuild plan, section 5.
"""

import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO

from . import events
from .server import record_api
from .service.protocol import Event, ProtocolError, Reply, Request, decode, encode

_area: list[tuple[int, int, int, int] | None] = [None]  # the recorder's pill on screen: its clicks aren't recorded


def _start(params: dict) -> object:
    return record_api.start(Path(str(params["path"])), str(params["name"]), bool(params.get("replace", False)))


def _check(params: dict) -> object:
    return record_api.add_check(dict(params))


def _stop(params: dict) -> object:
    return record_api.stop(bool(params.get("keep", True)))


def _area_is(params: dict) -> object:
    box = params.get("area")
    _area[0] = tuple(int(value) for value in box) if box and box[2] > 0 else None
    return {"area": box}


def _keys(params: dict) -> object:
    record_api.shortcuts = dict(params.get("keys", {}))
    return {"keys": record_api.shortcuts}


METHODS: dict[str, Callable[[dict], object]] = {
    "record.start": _start,
    "record.status": lambda params: record_api.status(),
    "record.pause": lambda params: record_api.pause(),
    "record.mark": lambda params: record_api.mark(),
    "record.check": _check,
    "record.remove_last": lambda params: record_api.remove_last(),
    "record.stop": _stop,
    "record.area": _area_is,
    "record.keys": _keys,
}


def serve(reader: BinaryIO, writer: BinaryIO) -> None:
    """Answer requests from `reader` on `writer` until `reader` ends, sending record.tick events as they come."""
    lock = threading.Lock()

    def send(message: Reply | Event) -> None:
        with lock:
            writer.write(encode(message))
            writer.flush()

    def forward(topic: str, data: dict) -> None:
        if topic == "record.tick":
            send(Event(topic, data))

    record_api.ignore_area = _ignored
    stop_listening = events.listen(forward)
    try:
        for line in reader:
            try:
                message = decode(line)
            except ProtocolError as error:
                send(Reply(0, error=str(error)))
                continue
            if isinstance(message, Request):
                send(_answer(message))
    finally:
        stop_listening()
        if record_api._recording is not None:
            record_api.stop(False)  # the Studio went away mid-recording: let go of everything, keep nothing


def _answer(request: Request) -> Reply:
    method = METHODS.get(request.method)
    if method is None:
        return Reply(request.id, error=f"no method called {request.method}")
    try:
        return Reply(request.id, method(request.params))
    except (ValueError, KeyError, OSError, RuntimeError) as error:  # RuntimeError: no listener on this system
        return Reply(request.id, error=str(error) or type(error).__name__)


def _ignored() -> tuple[int, int, int, int] | None:
    return _area[0]


def main() -> int:
    serve(sys.stdin.buffer, sys.stdout.buffer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
