"""The messages between darbit's service and its clients: one JSON object per line on a local socket.

A client sends `hello` with the token from the service's address file, then requests; the service answers each
with a reply carrying the same id, and sends events (a bot started, a report line came in) as they happen.

    {"type": "hello", "token": "...", "client": "darbit cli", "version": 1}
    {"type": "request", "id": 1, "method": "bots.list", "params": {}}
    {"type": "reply", "id": 1, "result": [...]}                 # or "error": "...", maybe with "code" and "detail"
    {"type": "event", "topic": "bot.status", "data": {...}}

Any language can speak it, so the Studio, a phone bridge, the VS Code extension or MCP use the same channel.
"""

import json
from dataclasses import asdict, dataclass, field, fields

VERSION = 1
HOST = "127.0.0.1"


class ProtocolError(ValueError):
    """A line that isn't one of darbit's messages."""


@dataclass
class Hello:
    token: str
    client: str = ""
    version: int = VERSION


@dataclass
class Request:
    id: int
    method: str
    params: dict = field(default_factory=dict)


@dataclass
class Reply:
    id: int
    result: object = None
    error: str | None = None
    code: str | None = None  # a refusal a client can act on, e.g. "input_bot_running"; sent only when set
    detail: dict | None = None  # what goes with the code, e.g. {"running": [the bots in the way]}


@dataclass
class Event:
    topic: str
    data: dict = field(default_factory=dict)


Message = Hello | Request | Reply | Event
TYPES: dict[str, type] = {"hello": Hello, "request": Request, "reply": Reply, "event": Event}
NAMES = {kind: name for name, kind in TYPES.items()}


def encode(message: Message) -> bytes:
    """One line of JSON, ending in a line break."""
    data = {"type": NAMES[type(message)]}
    data.update(asdict(message))
    if isinstance(message, Reply):
        for name in ("code", "detail"):
            if data[name] is None:
                del data[name]  # a reply without them reads the same to an older client
    return (json.dumps(data, separators=(",", ":"), default=str) + "\n").encode("utf-8")


def decode(line: bytes | str) -> Message:
    """The message on one line; ProtocolError if it isn't one."""
    try:
        data = json.loads(line)
    except ValueError as error:
        raise ProtocolError(f"not JSON: {error}") from error
    if not isinstance(data, dict):
        raise ProtocolError("a message is a JSON object")
    kind = TYPES.get(str(data.pop("type", "")))
    if kind is None:
        raise ProtocolError("unknown message type")
    known = {item.name for item in fields(kind)}
    given = {name: value for name, value in data.items() if name in known}  # a newer service's fields are skipped
    try:
        return kind(**given)
    except TypeError as error:
        raise ProtocolError(f"wrong fields: {error}") from error
