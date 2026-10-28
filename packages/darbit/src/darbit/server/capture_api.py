"""The web capture tool's requests: the frozen shot as a frame, boxes around a click, Test, and Save.

The work is in capture/service.py; this turns it into requests and frames. Opening and closing the capture
window is the desktop's job (desktop/capture_window.py), which hooks `on_close`. Decision 0013, round 7.
"""

from collections.abc import Callable

from ..capture import service
from .events import publish
from .frames import Frame, encode

on_close: Callable[[], None] | None = None  # set by the desktop: close the window and bring the Studio back
on_next: Callable[[], None] | None = None  # hide the overlay and show the bar naming the next picture
on_refreeze: Callable[[], None] | None = None  # hide, grab the screen again, show the overlay


def session(data: dict) -> dict:
    """What this capture is for: the items still to take."""
    current = service._current()
    return {"items": service.describe(current.items), "folder": current.images.name, "test": current.test}


def frame(data: dict) -> Frame:
    """The frozen shot, as raw pixels."""
    current = service._current()
    if current.shot is None or current.origin is None:
        raise service.CaptureError("nothing frozen yet")
    return encode(current.shot, {"x": current.origin.x, "y": current.origin.y})


def candidates(data: dict) -> dict:
    return service.candidates(int(data.get("x", 0)), int(data.get("y", 0)), str(data.get("kind", "image")))


def test(data: dict) -> dict:
    similarity = float(data.get("similarity") or 0.8)
    return service.test(data.get("box"), data.get("name"), data.get("region"), similarity)


def save(data: dict) -> dict:
    name = str(data.get("name", ""))
    saved = service.save(name, str(data.get("kind", "image")), data.get("image"), data.get("region"), data.get("point"))
    publish("library.changed", {"path": str(service._current().project), "names": [name]})  # the Library redraws it
    return saved


def next_item(data: dict) -> dict:
    """Between guide items: the desktop hides the overlay until the next screen is frozen."""
    if on_next is not None:
        on_next()
    return {"waiting": True}


def refreeze(data: dict) -> dict:
    """Freeze the screen again (Space in the overlay, the bar's button, or Ctrl+Alt+C)."""
    if on_refreeze is not None:
        on_refreeze()
    else:
        service.freeze()
    return {"frozen": True}


def close(data: dict) -> dict:
    """Leave capture: the desktop closes the window and shows the Studio again."""
    service.stop()
    if on_close is not None:
        on_close()
    return {"closed": True}


def register() -> None:
    from .app import HANDLERS

    HANDLERS["capture.session"] = session
    HANDLERS["capture.frame"] = frame
    HANDLERS["capture.candidates"] = candidates
    HANDLERS["capture.test"] = test
    HANDLERS["capture.save"] = save
    HANDLERS["capture.next"] = next_item
    HANDLERS["capture.refreeze"] = refreeze
    HANDLERS["capture.close"] = close
