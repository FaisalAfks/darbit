"""Playing an action from darbit Studio: call its function and follow it line by line (decision 0010, T16).

There's no interpreter: playing is calling the @d.flow function. A trace on the thread that plays it reports
each line of the action files as it runs, stops at breakpoints, steps one line at a time, and stops when asked
(raising Stopped inside the action, as the stop hotkey does). See docs/tasks/T16-player-run-panel.md.
"""

import importlib
import sys
import threading
from collections.abc import Callable
from pathlib import Path

from ..errors import Stopped
from ..platform import input as device
from ..platform import safety
from ..runtime import tape

OnLine = Callable[[str, int], None]  # (action file's name without .py, line)


class Player:
    """Plays one action on its own thread. `breakpoints` maps an action's name to its lines."""

    def __init__(
        self, project: Path, name: str, on_line: OnLine, on_pause: OnLine, on_end: Callable[[str, str], None]
    ) -> None:
        self.project = project
        self.folder = project / "actions"
        self.name = name
        self.on_line = on_line
        self.on_pause = on_pause
        self.on_end = on_end
        self.breakpoints: dict[str, set[int]] = {}
        self.resume_event = threading.Event()
        self.stopping = threading.Event()
        self.stepping = False
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        tape.stopping.clear()
        safety.reset()  # Ctrl+Alt+Q stopped the last one; this one may still play
        self.thread = threading.Thread(target=self._play, name=f"darbit-play-{self.name}", daemon=True)
        self.thread.start()

    def resume(self) -> None:
        self.stepping = False
        self.resume_event.set()

    def step(self) -> None:
        """Run one line, then pause again."""
        self.stepping = True
        self.resume_event.set()

    def stop(self) -> None:
        self.stopping.set()
        tape.stopping.set()  # a tape that's playing ends at its next event
        self.resume_event.set()

    def _load(self) -> Callable[[], object]:
        """Import actions/<name>.py fresh (edits since the last play count), as part of the `actions` package."""
        for module in list(sys.modules):
            if module == "actions" or module.startswith("actions."):
                del sys.modules[module]
        if str(self.project) not in sys.path:
            sys.path.insert(0, str(self.project))
        importlib.invalidate_caches()
        module = importlib.import_module(f"actions.{self.name}")
        function = vars(module).get(self.name)  # the function named like its file
        if function is None:
            raise AttributeError(f"actions/{self.name}.py has no function called {self.name}")
        return function

    def _play(self) -> None:
        status = "done"
        reason = ""
        try:
            function = self._load()
            sys.settrace(self._trace)
            try:
                function()
            finally:
                sys.settrace(None)
                device.release_all()  # a stop or a failure mid-hold mustn't leave keys down
        except Stopped:
            status = "stopped"
        except Exception as error:  # noqa: BLE001 - the Studio shows why the action failed
            status = "failed"
            reason = f"{type(error).__name__}: {error}"
        self.on_end(status, reason)

    def _trace(self, frame: object, event: str, arg: object) -> Callable | None:
        filename = Path(frame.f_code.co_filename)
        if filename.parent != self.folder:
            return None  # darbit's own code and anything else: not followed
        if event == "line":
            self._line(filename.stem, frame.f_lineno)
        return self._trace

    def _line(self, action: str, line: int) -> None:
        if self.stopping.is_set():
            raise Stopped("stopped from darbit Studio")
        self.on_line(action, line)
        if self.stepping or line in self.breakpoints.get(action, set()):
            self.resume_event.clear()
            self.on_pause(action, line)
            self.resume_event.wait()
            if self.stopping.is_set():
                raise Stopped("stopped from darbit Studio")
