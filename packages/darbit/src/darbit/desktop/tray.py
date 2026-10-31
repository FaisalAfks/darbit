"""darbit's icon in the Windows tray: open the Studio, control a running bot, quit.

Built on Windows Forms' NotifyIcon through pythonnet, which pywebview already loads, so it needs nothing more.
The icon is darbit's logo (desktop/darbit.ico), with a green dot while a bot runs.
Double-click opens the Studio; right-click shows a menu made fresh each time it opens. See decision 0013.
"""

import threading
from collections.abc import Callable

from ..server import hub
from ..server.events import publish
from .pill import RunPill
from .windows import ICON, Window

ICON_SIZE = 32  # px, made once per state and scaled by Windows
RUNNING_DOT = (74, 222, 128)


class Tray:
    """The tray icon for one Studio window. `start()` runs on the window's UI thread once it's shown."""

    def __init__(self, studio: Window, run_pill: RunPill) -> None:
        self.studio = studio
        self.run_pill = run_pill
        self.icon = None
        self.icons: dict[bool, object] = {}  # running? -> its System.Drawing.Icon
        self.on_quit: Callable[[], None] | None = None

    # ---- set up, on the UI thread

    def start(self) -> None:
        """Create the icon on the Studio form's thread (Windows Forms needs its message loop)."""
        from System import Action

        form = self.studio.native.native
        form.Invoke(Action(self._create))

    def _create(self) -> None:
        import clr

        clr.AddReference("System.Windows.Forms")
        from System import EventHandler
        from System.Windows import Forms

        self.icon = Forms.NotifyIcon()
        self.icon.Text = "darbit Studio"
        self.icon.Icon = self._picture(False)
        menu = Forms.ContextMenuStrip()
        menu.Opening += self._fill_menu
        self.icon.ContextMenuStrip = menu
        self.icon.DoubleClick += EventHandler(self._double_click)
        self.icon.Visible = True
        follow_events(self._status_changed)

    def _picture(self, running: bool) -> object:
        """darbit's icon, with a green dot while a bot runs."""
        if running in self.icons:
            return self.icons[running]
        import clr

        clr.AddReference("System.Drawing")
        from System.Drawing import Bitmap, Color, Graphics, Icon, Size, SolidBrush
        from System.Drawing.Drawing2D import SmoothingMode

        logo = Icon(str(ICON), Size(ICON_SIZE, ICON_SIZE))
        picture = Bitmap(logo.ToBitmap(), ICON_SIZE, ICON_SIZE)
        logo.Dispose()
        canvas = Graphics.FromImage(picture)
        canvas.SmoothingMode = SmoothingMode.AntiAlias
        if running:
            outline = SolidBrush(Color.FromArgb(32, 32, 32))
            dot = SolidBrush(Color.FromArgb(RUNNING_DOT[0], RUNNING_DOT[1], RUNNING_DOT[2]))
            canvas.FillEllipse(outline, 17, 17, 15, 15)
            canvas.FillEllipse(dot, 19, 19, 11, 11)
        canvas.Dispose()
        icon = Icon.FromHandle(picture.GetHicon())
        self.icons[running] = icon
        return icon

    # ---- the menu, made fresh each time it opens

    def _fill_menu(self, sender: object, args: object) -> None:
        from System import EventHandler
        from System.Drawing import Font, FontStyle
        from System.Windows import Forms

        menu = sender
        menu.Items.Clear()
        open_item = Forms.ToolStripMenuItem("Open darbit Studio", None, EventHandler(self._open))
        open_item.Font = Font(open_item.Font, FontStyle.Bold)
        menu.Items.Add(open_item)
        running = hub.running()
        if running:
            folder = running[0]
            menu.Items.Add(Forms.ToolStripSeparator())
            title = Forms.ToolStripMenuItem(f"{folder.name} · {hub.status(folder)}")
            title.Enabled = False
            menu.Items.Add(title)
            pause_text = "Resume" if hub.status(folder) == "paused" else "Pause"
            menu.Items.Add(Forms.ToolStripMenuItem(pause_text, None, EventHandler(self._pause)))
            menu.Items.Add(Forms.ToolStripMenuItem("Stop", None, EventHandler(self._stop)))
            menu.Items.Add(Forms.ToolStripMenuItem("Show the pill", None, EventHandler(self._show_pill)))
        menu.Items.Add(Forms.ToolStripSeparator())
        menu.Items.Add(Forms.ToolStripMenuItem("Studio settings", None, EventHandler(self._settings)))
        quit_text = "Quit darbit"
        if running:
            quit_text = f"Quit darbit (stops {running[0].name})"
        menu.Items.Add(Forms.ToolStripMenuItem(quit_text, None, EventHandler(self._quit_clicked)))
        args.Cancel = False

    # ---- what the menu does (slow work goes to a thread, never the UI thread)

    def _double_click(self, sender: object, args: object) -> None:
        self._open(sender, args)

    def _open(self, sender: object, args: object) -> None:
        background(self.show_studio)

    def show_studio(self) -> None:
        if self.run_pill.collapsed.is_set():
            self.run_pill.expand({})
        else:
            self.studio.show()

    def _pause(self, sender: object, args: object) -> None:
        background(self._pause_running)

    def _pause_running(self) -> None:
        running = hub.running()
        if running:
            hub.project_pause({"path": str(running[0])})

    def _stop(self, sender: object, args: object) -> None:
        background(self._stop_running)

    def _stop_running(self) -> None:
        running = hub.running()
        if running:
            hub.project_stop({"path": str(running[0])})

    def _show_pill(self, sender: object, args: object) -> None:
        background(self._collapse)

    def _collapse(self) -> None:
        running = hub.running()
        if running:
            self.run_pill.collapse({"path": str(running[0])})

    def _settings(self, sender: object, args: object) -> None:
        background(self._open_settings)

    def _open_settings(self) -> None:
        self.show_studio()
        publish("studio.page", {"page": "studio-settings"})

    def _quit_clicked(self, sender: object, args: object) -> None:
        background(self.quit)

    def quit(self) -> None:
        """Stop running bots, remove the icon and close every window, which ends `darbit app`."""
        import webview

        if self.on_quit is not None:
            self.on_quit()
        hub.stop_all()
        self._remove()
        for window in list(webview.windows):
            window.destroy()

    def _remove(self) -> None:
        if self.icon is None:
            return
        from System import Action

        form = self.studio.native.native
        form.Invoke(Action(self._hide_icon))

    def _hide_icon(self) -> None:
        self.icon.Visible = False
        self.icon.Dispose()

    # ---- the dot follows the bots

    def _status_changed(self, topic: str, data: dict) -> None:
        if topic != "project.status" or self.icon is None:
            return
        from System import Action

        form = self.studio.native.native
        form.Invoke(Action(self._redraw))

    def _redraw(self) -> None:
        running = bool(hub.running())
        self.icon.Icon = self._picture(running)
        self.icon.Text = "darbit Studio · a bot is running" if running else "darbit Studio"


def background(work: Callable[[], None]) -> None:
    """Run `work` on its own thread, so the tray's menu never waits."""
    threading.Thread(target=work, name="darbit-tray", daemon=True).start()


def follow_events(listener: Callable[[str, dict], None]) -> None:
    """Get every event, to follow bots starting and stopping."""
    from .. import events

    events.listen(listener)
