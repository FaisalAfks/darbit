"""The keys darbit settings lets you change: only those the Studio really goes by, each with its plain name.

`rows()` gives them with their keys now and their defaults; `clash()` says what else already uses a key, among those
that can be pressed at the same time. The keys themselves live in keymap.py.
"""

from .. import keymap

# (action, what it does, where it works)
EDITABLE = [
    ("palette.open", "Command palette", "In the Studio"),
    ("run.toggle", "Play the bot", "In the Studio"),
    ("page.overview", "Overview", "In the Studio"),
    ("page.library", "Library", "In the Studio"),
    ("page.results", "Results", "In the Studio"),
    ("page.settings", "Settings", "In the Studio"),
    ("page.darbit", "darbit settings", "In the Studio"),
    ("bot.new", "New bot", "In the Studio"),
    ("search", "Search the page", "In the Studio"),
    ("file.save", "Save", "In the Studio"),
    ("capture.freeze", "Capture", "With the game in front"),
    ("scout.toggle", "Scout", "With the game in front"),
    ("scout.next", "Scout: next image", "While Scout is on"),
    ("scout.previous", "Scout: image before", "While Scout is on"),
    ("record.mark", "Recording: checkpoint", "With the game in front"),
    ("run.pause", "Recording: pause", "With the game in front"),
]


def _defaults() -> dict[str, str]:
    flat: dict[str, str] = {}
    for actions in keymap.defaults().values():
        flat.update({action: str(keys) for action, keys in actions.items()})
    return flat


def rows() -> list[dict]:
    """Each key to show: {action, label, where, keys, default}."""
    defaults = _defaults()
    found = []
    for action, label, where in EDITABLE:
        found.append(
            {
                "action": action,
                "label": label,
                "where": where,
                "keys": keymap.combo(action),
                "default": defaults.get(action, ""),
            }
        )
    return found


def now() -> dict[str, str]:
    """Each action's keys now, for the Studio's shortcuts."""
    return {action: keymap.combo(action) for action, _, _ in EDITABLE}


def clash(action: str, keys: str) -> str:
    """What else uses these keys (a key working with the game in front also works in the Studio), or ""."""
    if not keys:
        return ""
    for other, label, _ in EDITABLE:
        if other != action and keymap.combo(other) == keys:
            return label
    return ""
