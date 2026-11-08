"""Mouse and keyboard, through the system's Input piece (platform/backend.py).

The mouse glides to a spot and sends real move events all the way; keys go by their position on the keyboard,
whatever its language; a short pause follows every press and release. The tape's input (key_now, button_now,
nudge, place, wheel_now) goes at once, with no pause.
"""

from . import backend, ghost, real


def position() -> tuple[int, int]:
    return backend.input().position()


def desktop() -> tuple[int, int, int, int]:
    """Every screen together: x, y, width, height."""
    return backend.input().desktop()


def move(x: int, y: int, glide: float) -> None:
    """Glide the cursor to (x, y) in `glide` seconds (0 jumps)."""
    real.refuse("input.move")
    backend.input().move(x, y, glide)


def move_by(dx: int, dy: int, seconds: float) -> None:
    """Move the mouse by (dx, dy) counts, spread over `seconds`."""
    real.refuse("input.move_by")
    backend.input().move_by(dx, dy, seconds)


def mouse_down(button: str = "left") -> None:
    real.refuse("input.mouse_down")
    _tell_here("click", button=button)
    backend.input().mouse_down(button)


def mouse_up(button: str = "left") -> None:
    real.refuse("input.mouse_up")
    backend.input().mouse_up(button)


def click(x: int, y: int, glide: float, button: str = "left", times: int = 1) -> None:
    real.refuse("input.click")
    ghost.tell("click", x=x, y=y, button=button)  # before the glide: the ghost shows where the cursor is going
    backend.input().click(x, y, glide, button, times)


def drag(from_x: int, from_y: int, to_x: int, to_y: int, glide: float) -> None:
    real.refuse("input.drag")
    backend.input().drag(from_x, from_y, to_x, to_y, glide)


def scroll(notches: int) -> None:
    """Positive scrolls up, negative scrolls down."""
    real.refuse("input.scroll")
    backend.input().scroll(notches)


def key_down(what: object) -> None:
    real.refuse("input.key_down")
    _tell_here("key", name=_name(what))
    backend.input().key_down(what)


def key_up(what: object) -> None:
    real.refuse("input.key_up")
    backend.input().key_up(what)


def tap(what: object) -> None:
    real.refuse("input.tap")
    _tell_here("key", name=_name(what))
    backend.input().tap(what)


def write(text: str) -> None:
    """Type characters, whatever keyboard language is active."""
    real.refuse("input.write")
    _tell_here("key", name=text)
    backend.input().write(text)


def key_now(what: object, up: bool) -> None:
    """A key down or up, sent at once with no pause after it."""
    real.refuse("input.key_now")
    if not up:
        _tell_here("key", name=_name(what))
    backend.input().key_now(what, up)


def button_now(button: str, up: bool) -> None:
    real.refuse("input.button_now")
    if not up:
        _tell_here("click", button=button)
    backend.input().button_now(button, up)


def nudge(dx: int, dy: int) -> None:
    """One relative mouse packet, like the mouse sends."""
    real.refuse("input.nudge")
    backend.input().nudge(dx, dy)


def place(x: int, y: int) -> None:
    """Put the cursor at (x, y) at once."""
    real.refuse("input.place")
    backend.input().place(x, y)


def wheel_now(notches: int, sideways: bool = False) -> None:
    real.refuse("input.wheel_now")
    backend.input().wheel_now(notches, sideways)


def _tell_here(kind: str, **data: object) -> None:
    """Tell the ghost cursor, at the cursor's place now."""
    if ghost.listening():
        x, y = position()
        ghost.tell(kind, x=x, y=y, **data)


def _name(what: object) -> str:
    return str(getattr(what, "name", what))


def release_all() -> None:
    """Let go of every key and mouse button darbit is holding (nothing to do if no input was ever sent)."""
    if backend.loaded("input"):
        backend.input().release_all()


def let_go_of_everything() -> None:
    """Send a release for every key and mouse button, held or not."""
    real.refuse("input.let_go_of_everything")
    backend.input().let_go_of_everything()
