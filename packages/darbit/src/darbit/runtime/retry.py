"""Keep trying a step: when it fails (d.Failed) or an observer interrupts it, record why, recover, and go again.

    def attempt():
        if not d.click("Menu.Start"):
            raise d.Failed("no Start button")

    d.keep_trying("Daily quest", attempt, recover=restart_the_game, go_on=quests_left, back_to="Menu")

With `back_to`, a failure first goes back to that screen of the map and tries again; `recover` runs when that
doesn't help. Every try is a step in the run report; every recovery shows on the Results page.
"""

import traceback
from collections.abc import Callable

from ..errors import Failed, Interrupted, Stopped
from ..platform.safety import no_interrupts
from . import screens as screen_map
from .log import log
from .show import Record
from .steps import step

_record = Record()


def keep_trying(
    name: str,
    attempt: Callable[[], None],
    recover: Callable[[], None],
    go_on: Callable[[], bool] | None = None,
    how: str = "recover",
    back_to: str | None = None,
    screens: screen_map.Map | None = None,
    back_timeout: float | None = None,
) -> bool:
    """Run `attempt` as a step called `name` until it returns. When it raises Failed or is interrupted, `recover` is
    called (with observers muted, so a restart doesn't trip them) and it's tried again. `go_on`, asked before each
    try, ends it early when it says no. `how` names the recovery on the Results page ("restart", "rejoin").

    `back_to` names a screen of the map (`screens`, or `d.screens`) to go back to before recovering: after a
    failure it goes there and tries again, and only recovers when that try fails too or the way back is lost.
    `back_timeout` is how long the way back waits for each screen (`go`'s timeout; None is `settings.timeout`), so a
    bot that's clearly lost recovers sooner.

    True once the attempt went through, False when `go_on` said stop."""
    went_back = False  # the last try came right after a go-back
    while True:
        if go_on is not None and not go_on():
            return False
        try:
            with step(name):
                attempt()
            return True
        except Failed as reason:
            why = f"{name}: {reason}"
        except Interrupted as event:
            why = f"{name}: {event.name}"
            _record("watchdog", what=event.name, step=name)
        if back_to is not None and not went_back and _go_back(back_to, screens, back_timeout, why):
            went_back = True
            continue
        log(f"{why}; {how}")
        _record.recovered(how, why)
        with no_interrupts():
            recover()
        went_back = False


def _go_back(screen: str, screens: screen_map.Map | None, timeout: float | None, why: str) -> bool:
    """Go to `screen` with observers muted and record it as a recovery; False when the way there is lost. A move
    that raises (a bug in one move, say a picture saved without an area) is a way back that didn't work: it's logged
    with its traceback and counts as lost, so the bot recovers instead of ending. Stopping still stops."""
    world = screen_map.default if screens is None else screens
    try:
        with no_interrupts():
            arrived = world.go(screen, timeout)
    except Stopped:
        raise
    except Exception as error:  # noqa: BLE001 - one broken move must not end the bot (#484)
        log(f"{why}; the way back to {screen} broke: {type(error).__name__}: {error}")
        log(traceback.format_exc().rstrip())
        return False
    if not arrived:
        log(f"{why}; can't get back to {screen}")
        return False
    log(f"{why}; back to {screen}")
    _record.recovered(f"back to {screen}", why)
    return True
