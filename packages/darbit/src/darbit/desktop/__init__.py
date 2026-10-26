"""Desktop windows for the UI apps: the hub, the capture overlay, highlight, the recorder bar, the run panel.

    open_window("hub", "normal")
    open_window("recorder", "bar")            # on top, never takes focus from the game
    open_window("highlight", "clickthrough")  # the mouse goes through it

Needs the `app` extra. See docs/tasks/T06-desktop-windows.md.
"""

from .windows import Kind, Window, open_window, styles

__all__ = ["Kind", "Window", "open_window", "styles"]
