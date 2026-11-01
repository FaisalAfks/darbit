"""The ghost cursor (#117): where the bot clicks and which keys it presses, told to darbit Studio, which shows them
over the game so a person can see what the bot is doing (and that it's the bot, not them).

Each click or key is one small UDP message to the port the Studio wrote in its ghost file (data_dir/ghost.json).
Nothing waits for it: no Studio listening, and the message is simply lost. The file is looked at again every few
seconds, so a Studio opened after the bot started still gets them.
"""

import json
import socket
import time

from .. import paths

FILE = "ghost.json"
LOOK_EVERY = 3.0  # seconds between looks at the ghost file

_port: list[int | None] = [None]
_looked: list[float] = [-LOOK_EVERY]
_socket: list[socket.socket | None] = [None]


def path() -> object:
    return paths.data_dir() / FILE


def tell(kind: str, **data: object) -> None:
    """Tell the Studio, if it's listening: `click` (x, y, button) or `key` (name, x, y)."""
    port = _listening()
    if port is None:
        return
    data["kind"] = kind
    try:
        if _socket[0] is None:
            _socket[0] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            _socket[0].setblocking(False)
        _socket[0].sendto(json.dumps(data).encode("utf-8"), ("127.0.0.1", port))
    except OSError:
        pass  # the Studio went away (Windows answers a closed port with an error on a later send): nothing lost


def listening() -> bool:
    """Whether a Studio is listening (as of the last look)."""
    return _listening() is not None


def _listening() -> int | None:
    now = time.monotonic()
    if now - _looked[0] >= LOOK_EVERY:
        _looked[0] = now
        _port[0] = _read_port()
    return _port[0]


def _read_port() -> int | None:
    try:
        port = int(json.loads(path().read_text(encoding="utf-8"))["port"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if 0 < port < 65536:
        return port
    return None


def forget() -> None:
    """Look at the ghost file again at the next input (for tests)."""
    _looked[0] = -LOOK_EVERY
