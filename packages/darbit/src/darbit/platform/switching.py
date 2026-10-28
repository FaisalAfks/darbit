"""Quick switching between Python threads while input is recorded or played.

Python runs one thread at a time and by default lets another have a turn only every 5 ms. With darbit Studio's
other threads busy, the recorder's raw input thread then fell behind and mouse counts were lost (38 of 200 in a
test), and a tape's events went out late. While recording or playing, threads switch every 0.5 ms instead.

    done = fast()
    ...                # record or play
    done()             # back to how it was, once nothing else needs it
"""

import sys
import threading
from collections.abc import Callable

FAST = 0.0005  # seconds a thread runs before another gets a turn

_lock = threading.Lock()
_users = 0
_before = 0.005


def fast() -> Callable[[], None]:
    """Switch threads quickly until the returned function is called."""
    global _users, _before
    with _lock:
        if _users == 0:
            _before = sys.getswitchinterval()
            sys.setswitchinterval(FAST)
        _users += 1
    finished = threading.Event()

    def done() -> None:
        global _users
        if finished.is_set():
            return
        finished.set()
        with _lock:
            _users -= 1
            if _users == 0:
                sys.setswitchinterval(_before)

    return done
