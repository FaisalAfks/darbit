"""Keep trying a step: when it fails (d.Failed) or an observer interrupts it, record why, recover, and go again.

    def attempt():
        if not d.click("Menu.Start"):
            raise d.Failed("no Start button")

    d.keep_trying("Daily quest", attempt, recover=restart_the_game, go_on=quests_left)

Every try is a step in the run report (timed, failures saved with a screenshot); every recovery shows on the
Results page.
"""

from collections.abc import Callable

from ..errors import Failed, Interrupted
from ..platform.safety import no_interrupts
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
) -> bool:
    """Run `attempt` as a step called `name` until it returns. When it raises Failed or is interrupted, `recover` is
    called (with observers muted, so a restart doesn't trip them) and it's tried again. `go_on`, asked before each
    try, ends it early when it says no. `how` names the recovery on the Results page ("restart", "rejoin").

    True once the attempt went through, False when `go_on` said stop."""
    while True:
        if go_on is not None and not go_on():
            return False
        try:
            with step(name):
                attempt()
            return True
        except Failed as reason:
            log(f"{name}: {reason}; {how}")
            _record.recovered(how, f"{name}: {reason}")
        except Interrupted as event:
            log(f"{name}: {event.name}; {how}")
            _record("watchdog", what=event.name, step=name)
            _record.recovered(how, f"{name}: {event.name}")
        with no_interrupts():
            recover()
