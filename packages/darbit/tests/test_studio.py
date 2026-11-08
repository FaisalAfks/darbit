"""darbit Studio: its theme tokens, what its pages bind to, and every page drawn offscreen with no QML warning.

Needs the studio extra (PySide6); skipped without it. The service is a fake client with canned answers.
"""

import os
import time
from pathlib import Path

import pytest

from darbit.studio import theme

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtCore = pytest.importorskip("PySide6.QtCore", exc_type=ImportError)

from PySide6.QtCore import Q_ARG, QMetaObject
from PySide6.QtGui import QGuiApplication

from darbit.studio import app, backend

BOT = {
    "path": "/bots/ad-bot",
    "name": "ad-bot",
    "version": "0.3.0",
    "accent": "#f472b6",
    "summary": "Raids",
    "installed": True,
    "status": "running",
    "since": time.time() - 3600,
}
ANSWERS = {
    "bots.list": [BOT, {**BOT, "path": "/bots/other", "name": "other", "status": "stopped", "since": None}],
    "bot.dashboard": {
        "project": BOT,
        "tiles": [
            {
                "kind": "now",
                "title": "Now",
                "data": {"path": ["Speed Raid", "Sakura"], "since": "2026-10-31T11:24:00.000"},
            },
            {
                "kind": "round",
                "title": "Today's round",
                "data": {
                    "steps": [
                        {"name": "Raid", "started": "2026-10-31T11:02:00.000", "state": "ok", "seconds": 2460},
                        {
                            "name": "Speed Raid",
                            "started": "2026-10-31T11:24:00.000",
                            "state": "running",
                            "seconds": None,
                        },
                        {"name": "AFK", "started": None, "state": "planned", "seconds": None},
                    ]
                },
            },
            {
                "kind": "progress",
                "title": "Progress",
                "data": {
                    "items": [
                        {"label": "Speed Raid this week", "done": 32, "total": 133},
                        {"label": "Boss Rush today", "done": 1, "total": 1},
                    ]
                },
            },
            {
                "kind": "gains",
                "title": "Gains today",
                "data": {"items": [{"name": "Gems", "today": 120, "total": 5400, "icon": None}]},
            },
            {
                "kind": "next",
                "title": "Next up",
                "data": {"items": [{"label": "Raid hour", "at": "2026-10-31T12:00:00", "in_seconds": 2040}]},
            },
            {
                "kind": "failures",
                "title": "Failures",
                "data": {
                    "items": [
                        {"time": "2026-10-31T09:12:00.000", "step": "AFK", "reason": "no rewards", "screenshot": None}
                    ]
                },
            },
        ],
    },
    "bot.library": [
        {
            "name": "Bag.Equip",
            "kind": "image",
            "group": "Bag",
            "thumbnail": None,
            "scores": [0.99],
            "similarity": 0.9,
            "missing": False,
        },
        {
            "name": "Bag.Gone",
            "kind": "image",
            "group": "Bag",
            "thumbnail": None,
            "scores": [],
            "similarity": None,
            "missing": True,
        },
    ],
    "bot.action.read": {
        "name": "dim_run",
        "docstring": "",
        "calls": [],
        "used_by": ["daily"],
        "breakpoints": [],
        "sections": [
            {
                "name": "Into the dimension",
                "line": 6,
                "steps": [
                    {
                        "kind": "key",
                        "args": {"verb": "press", "keys": ["e"]},
                        "note": "",
                        "line": 7,
                        "source": "",
                        "children": [],
                    },
                    {
                        "kind": "check",
                        "args": {"verb": "wait for", "target": "Dim.Start", "timeout": 30},
                        "note": "",
                        "line": 8,
                        "source": "",
                        "children": [],
                    },
                    {
                        "kind": "loop",
                        "args": {"times": 3},
                        "note": "",
                        "line": 9,
                        "source": "",
                        "children": [
                            {
                                "kind": "mouse",
                                "args": {"verb": "click", "target": "Dim.Go"},
                                "note": "",
                                "line": 10,
                                "source": "",
                                "children": [],
                            }
                        ],
                    },
                ],
            },
            {
                "name": "The run",
                "line": 11,
                "steps": [
                    {
                        "kind": "tape",
                        "args": {"start": 0, "end": 42.5},
                        "note": "",
                        "line": 12,
                        "source": "",
                        "children": [],
                    },
                    {
                        "kind": "wait",
                        "args": {"seconds": 0.5},
                        "note": "the loot",
                        "line": 13,
                        "source": "",
                        "children": [],
                    },
                    {
                        "kind": "call",
                        "args": {"name": "open_bag", "action": True},
                        "note": "",
                        "line": 14,
                        "source": "",
                        "children": [],
                    },
                ],
            },
        ],
    },
    "bot.actions": [{"name": "dim_run", "steps": 31, "sections": 2, "used_by": ["daily"]}],
    "bot.days": [
        {"day": "2026-10-31", "lead": {"name": "Gems", "amount": 120, "icon": None}, "seconds": 10800, "problems": 1}
    ],
    "bot.day": {
        "day": "2026-10-31",
        "start": 36000,
        "end": 46800,
        "week_days": [],
        "progress": [],
        "gains": [{"name": "Gems", "today": 120, "total": 5400, "icon": None, "week": []}],
        "finished": {"done": 2, "total": 3},
        "lost_seconds": 40,
        "problems": [
            {
                "step": "AFK",
                "path": "AFK",
                "reason": "no rewards",
                "count": 1,
                "times": ["2026-10-31T09:12:00.000"],
                "screenshot": None,
            }
        ],
        "lanes": [
            {"name": "Raid", "blocks": [{"start": 36000, "end": 38460, "state": "ok"}]},
            {"name": "Speed Raid", "blocks": [{"start": 40000, "end": None, "state": "running"}]},
        ],
    },
    "bot.settings": {
        "sections": [
            {
                "key": "modes",
                "label": "Modes",
                "help": "",
                "settings": [
                    {
                        "key": "modes.raid",
                        "type": "bool",
                        "default": True,
                        "label": "Raid",
                        "help": "Every round.",
                        "rules": {},
                    },
                    {
                        "key": "modes.every",
                        "type": "int",
                        "default": 30,
                        "label": "Every (minutes)",
                        "help": "",
                        "rules": {"min": 1},
                    },
                    {
                        "key": "modes.server",
                        "type": "choice",
                        "default": "a",
                        "label": "Server",
                        "help": "",
                        "rules": {"options": ["a", "b"]},
                    },
                ],
            }
        ],
        "values": {"modes.raid": True, "modes.every": 30, "modes.server": "a"},
        "error": None,
    },
}


def _overview_answer() -> dict:
    """The fake service's Overview as blocks, from the same tiles."""
    tiles = {tile["kind"]: tile["data"] for tile in ANSWERS["bot.dashboard"]["tiles"]}
    data = {"now": tiles["now"], "round": tiles["round"], "next": tiles["next"], "failures": tiles["failures"]}
    data["progress:Speed Raid this week"] = tiles["progress"]["items"][0]
    data["gain:Gems"] = {**tiles["gains"]["items"][0], "week": [10, 40, 0, 70, 30, 90, 120]}
    data["block:Boat"] = {"name": "Boat", "value": 7, "sub": "next upgrade at 2 000"}
    data["action:dim_run"] = {"name": "dim_run"}
    data["recoveries"] = {
        "count": 3,
        "reason": "disconnected",
        "reason_count": 2,
        "last": {"at": 40500, "how": "rejoin", "why": "disconnected"},
        "hows": [{"how": "rejoin", "count": 3, "whys": {"disconnected": 2, "stuck": 1}}],
    }
    layout = [
        {"kind": "now", "shows": "now", "title": "Now", "width": 8, "origin": "darbit"},
        {
            "kind": "ring",
            "shows": "progress:Speed Raid this week",
            "title": "Speed Raid this week",
            "width": 4,
            "origin": "darbit",
        },
        {"kind": "round", "shows": "round", "title": "Today's round", "width": 6, "origin": "darbit"},
        {"kind": "list", "shows": "next", "title": "Next up", "width": 6, "origin": "darbit"},
        {"kind": "number", "shows": "gain:Gems", "title": "Gems today", "width": 4, "origin": "darbit"},
        {"kind": "chart", "shows": "gain:Gems", "title": "Gems this week", "width": 4, "origin": "darbit"},
        {"kind": "number", "shows": "block:Boat", "title": "Boat", "width": 4, "origin": "ad-bot"},
        {"kind": "recoveries", "shows": "recoveries", "title": "Recoveries", "width": 4, "origin": "darbit"},
    ]
    extra = [
        {"kind": "list", "shows": "failures", "title": "Problems", "width": 6, "origin": "darbit"},
        {"kind": "button", "shows": "action:dim_run", "title": "dim_run", "width": 4, "origin": "ad-bot"},
    ]
    return {"project": BOT, "catalog": layout + extra, "layout": layout, "problem": "", "data": data}


ANSWERS["bot.overview"] = _overview_answer()
ANSWERS["bot.library.uses"] = []
ANSWERS["bot.doctor"] = {
    "checks": [
        {"name": "darbit.toml", "ok": True, "say": "ad-bot 1.0.0"},
        {"name": "game window", "ok": False, "say": "no window called Roblox: open it first"},
    ],
    "problems": 1,
}
ANSWERS["bot.library.screens"] = [
    {
        "screen": "Bag",
        "picture": "",
        "w": 1600,
        "h": 900,
        "assets": {
            "Bag.Equip": {"kind": "image", "box": [100, 100, 200, 60]},
            "Bag.Menu": {"kind": "region", "box": [50, 50, 900, 700]},
            "Bag.Spot": {"kind": "location", "box": [500, 500, 12, 12]},
        },
    }
]


class FakeClient:
    """The service, with the answers above; remembers what it was asked."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, dict]] = []

    def call(self, method: str, **params: object) -> object:
        self.asked.append((method, params))
        if method in ("bot.start", "bot.pause", "bot.stop"):
            return {"status": "running"}
        if method == "bot.settings.save":
            return {"saved": True}
        if method.startswith("bot.action.") and method not in ANSWERS:
            return {"playing": True}
        return ANSWERS[method]

    def on_event(self, listener: object) -> None:
        self.listener = listener


@pytest.fixture
def qt(monkeypatch, tmp_path):
    from darbit import paths

    monkeypatch.setattr(paths, "config_dir", lambda: tmp_path / "config")
    monkeypatch.setattr("darbit.service.client.ensure_running", lambda: None)
    return QGuiApplication.instance() or QGuiApplication(["test"])


def wait_until(check, seconds=5.0):
    deadline = time.monotonic() + seconds
    while not check() and time.monotonic() < deadline:
        QtCore.QCoreApplication.processEvents()
        time.sleep(0.01)
    assert check()


def test_css_colours_become_qt_colours():
    assert theme.qml_color("#5ac8fa") == "#ff5ac8fa"
    assert theme.qml_color("#fff") == "#ffffffff"
    assert theme.qml_color("rgb(22 25 33 / .74)") == "#bd161921"
    assert theme.qml_color("#11223380") == "#80112233"
    with pytest.raises(ValueError):
        theme.qml_color("blue-ish")


def test_a_custom_theme_lies_over_its_base(tmp_path):
    custom = tmp_path / "theme.toml"
    custom.write_text('base = "midnight"\naccent = "#ff7ab6"\naccent-2 = "nonsense"\n', encoding="utf-8")
    found = theme.colors("glass-dark", custom)
    assert found["accent"] == "#ffff7ab6"
    assert found["accent2"] == theme.qml_color(theme.THEMES["midnight"]["accent2"])  # a broken value keeps the base's
    assert found["bg"] == "#ff000000"
    assert set(theme.colors("glass-light")) == set(theme.colors("high-contrast"))  # every theme has every token


def test_the_pages_get_the_services_answers(qt):
    client = FakeClient()
    studio = backend.Studio(lambda: client, bot="other")
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "other")  # the bot asked for, not the first
    studio.selectBot("/bots/ad-bot")
    wait_until(lambda: len(studio.overview.get("layout", [])) == 8)
    assert not studio.libraryReady  # the Library says it's loading, not that there are no pictures
    studio.loadLibrary()
    studio.loadDays()
    studio.loadSettings()
    wait_until(lambda: studio.library and studio.days and studio.settings)
    assert studio.libraryReady
    studio.pause()
    wait_until(lambda: ("bot.pause", {"bot": "/bots/ad-bot"}) in client.asked)
    studio.saveSettings({"modes.raid": False})
    wait_until(lambda: ("bot.settings.save", {"bot": "/bots/ad-bot", "values": {"modes.raid": False}}) in client.asked)
    from darbit.server import ui_settings

    assert ui_settings.get(backend.CHOSEN) == "/bots/ad-bot"  # shown first next time


def test_a_refused_request_shows_its_reason(qt):
    from darbit.service.client import ServiceError

    class Refusing(FakeClient):
        def call(self, method, **params):
            if method == "bot.start":
                raise ServiceError("ad-bot is already running")
            return super().call(method, **params)

    studio = backend.Studio(Refusing)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    studio.start()
    wait_until(lambda: studio.message == "ad-bot is already running")


@pytest.mark.parametrize("theme_name", ["glass-dark", "high-contrast"])
@pytest.mark.parametrize("page", ["overview", "library", "results", "settings", "studio", "action"])
def test_every_page_draws_without_a_qml_warning(qt, tmp_path, page, theme_name):
    warnings = []

    def keep(kind, context, text):
        if kind != QtCore.QtMsgType.QtDebugMsg and ".qml" in text:  # the QML's own, not Qt's (fonts offscreen)
            warnings.append(text)

    QtCore.qInstallMessageHandler(keep)
    try:
        picture = tmp_path / f"{page}.png"
        app.shot(picture, page, theme_name, (1200, 800), connect=FakeClient)
    finally:
        QtCore.qInstallMessageHandler(None)
    assert picture.stat().st_size > 10_000
    assert warnings == []


def test_the_ghost_cursor_draws_without_a_qml_warning(qt, tmp_path):
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.ghost import Ghost

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        ghost = Ghost()
        engine = app.load(backend.Studio(FakeClient), ghost=ghost)
        root = engine.rootObjects()[0]  # held, or Qt deletes it
        ghost.take({"kind": "click", "x": 300, "y": 200, "button": "left"})
        ghost.take({"kind": "click", "x": 500, "y": 200, "button": "right"})
        ghost.take({"kind": "key", "x": 300, "y": 200, "name": "e"})
        ghost.take({"kind": "key", "x": 300, "y": 200, "name": "shift"})
        window = root.findChild(QQuickWindow, "ghostWindow")
        wait_until(lambda: window.isVisible() and len(ghost.marks) == 4)
        # only around the marks, not the whole screen
        assert window.width() < window.screen().size().width() / 2
        del engine
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


def test_the_ghost_cursor_shows_a_burst_of_marks_together(qt):
    from darbit.studio.ghost import Ghost

    ghost = Ghost()
    told = []
    ghost.changed.connect(lambda: told.append(len(ghost.marks)))
    for key in "12345":
        ghost.take({"kind": "key", "x": 300, "y": 200, "name": key})
    assert told == [1]  # the first at once, the rest wait for the next prune
    wait_until(lambda: told[-1] == 5)
    assert len(told) == 2


class NoBots(FakeClient):
    """A first start: the service has no bots yet."""

    def call(self, method: str, **params: object) -> object:
        if method == "bots.list":
            return []
        return super().call(method, **params)


def test_the_first_overview_welcomes_without_a_qml_warning(qt, tmp_path):
    warnings = []

    def keep(kind, context, text):
        if kind != QtCore.QtMsgType.QtDebugMsg and ".qml" in text:
            warnings.append(text)

    QtCore.qInstallMessageHandler(keep)
    try:
        app.shot(tmp_path / "welcome.png", "overview", connect=NoBots)
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


def test_capture_boxes_tests_and_saves_on_a_saved_screen(qt, tmp_path):
    import cv2
    import numpy as np

    from darbit.studio.capture import Capture, ShotProvider

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    screen = np.full((600, 900, 3), 30, np.uint8)
    cv2.rectangle(screen, (400, 300), (520, 350), (90, 200, 90), -1)  # a green button
    cv2.putText(screen, "PLAY", (420, 335), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    capture = Capture(ShotProvider())
    capture.start(tmp_path, shot=screen)
    assert capture.isOpen and (capture.shotWidth, capture.shotHeight) == (900, 600)
    assert capture.provider.image.width() == 900
    found = capture.candidates(450, 320, "image")
    box = found["boxes"][found["start"]]
    assert box[0] <= 400 and box[1] <= 300 and box[0] + box[2] >= 520 and box[1] + box[3] >= 350
    tested = capture.test(box, None)
    assert len(tested["matches"]) == 1 and tested["matches"][0]["score"] > 0.99
    assert capture.save("Lobby.Play", "image", box, None, None).get("error") is None
    assert (tmp_path / "images" / "Lobby.Play.png").is_file()
    assert capture.save("Lobby.Spot", "point", None, None, [10, 20]).get("error") is None
    assert capture.save("", "image", box, None, None)["error"] == "Give it a name first, in the pill"
    capture.close()
    assert not capture.isOpen


def test_the_capture_window_draws_a_box_and_matches_without_a_qml_warning(qt, tmp_path):
    import numpy as np
    from PySide6.QtCore import Q_ARG, QMetaObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.capture import Capture, ShotProvider

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
        screen = np.full((400, 600, 3), 30, np.uint8)
        screen[200:240, 300:400] = (90, 200, 90)
        capture = Capture(ShotProvider())
        engine = app.load(backend.Studio(FakeClient), capture)
        capture.start(tmp_path, shot=screen)
        root = engine.rootObjects()[0]  # held: a temporary root lets PySide drop its child windows
        window = root.findChild(QQuickWindow, "captureWindow")
        scale = window.property("scale")
        QMetaObject.invokeMethod(
            window, "clicked", Q_ARG("QVariant", 350 * scale), Q_ARG("QVariant", 220 * scale), Q_ARG("QVariant", True)
        )
        QMetaObject.invokeMethod(window, "test")
        wait_until(lambda: window.property("note").startswith("Found once"))  # after the scan sweeps
        assert window.property("note").startswith("Found once at 0.90 on the whole screen · nothing else close")
        assert window.grabWindow().width() > 0
        capture.close()
        QtCore.QCoreApplication.processEvents()
        del engine
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


def test_the_theme_chosen_is_used_next_time(qt):
    studio = backend.Studio(FakeClient)
    studio.setTheme("midnight")
    assert studio.colors["bg"] == "#ff000000"
    assert not studio.glass  # midnight draws no glass
    assert backend.Studio(FakeClient).themeName == "midnight"
    studio.setTheme("no such theme")
    assert studio.themeName == theme.DEFAULT


def test_the_look_switches_are_kept_and_read_from_memory(qt, monkeypatch):
    studio = backend.Studio(FakeClient)
    studio.setGhost(False)
    studio.setEffects(False)
    studio.setSidebar(True)
    with monkeypatch.context() as patch:
        patch.setattr(backend.ui_settings, "read_all", lambda: pytest.fail("read the settings file again"))
        assert (studio.ghost, studio.effects, studio.sidebar) == (False, False, True)
    assert (backend.Studio(FakeClient).ghost, backend.Studio(FakeClient).sidebar) == (False, True)


def worker_in_a_thread():
    """The input worker's loop on a thread, joined to a link by two pipes (so this test's fakes apply)."""
    import os
    import threading

    from darbit import worker
    from darbit.studio.worker_link import WorkerLink

    to_worker_read, to_worker_write = os.pipe()
    from_worker_read, from_worker_write = os.pipe()
    reader, writer = os.fdopen(to_worker_read, "rb"), os.fdopen(from_worker_write, "wb")
    threading.Thread(target=worker.serve, args=(reader, writer), daemon=True).start()
    return WorkerLink(lambda topic, data: None, (os.fdopen(from_worker_read, "rb"), os.fdopen(to_worker_write, "wb")))


def test_the_recorder_records_checks_and_saves_an_action(qt, tmp_path, monkeypatch):
    from darbit.platform import hooks
    from darbit.platform import input as device
    from darbit.server import record_api
    from darbit.studio.recorder import Recorder

    monkeypatch.setattr(hooks, "start", lambda on_event, moves=False: lambda: None)
    monkeypatch.setattr(device, "desktop", lambda: (0, 0, 1920, 1080))
    monkeypatch.setattr(device, "position", lambda: (0, 0))
    monkeypatch.setattr(record_api.tape, "_window_now", lambda: None)
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "rec-bot"\n', encoding="utf-8")
    recorder = Recorder(worker_in_a_thread())
    saved = []
    recorder.finished.connect(saved.append)
    assert recorder.start(tmp_path, "9 lives") != ""  # not a name an action can have
    assert recorder.start(tmp_path, "open_bag") == ""
    assert recorder.active and recorder.name == "open_bag"
    started = record_api._recording.started
    at = int(started * 1e9)
    record_api._on_event("key_down", 0x45, 0, 0, at + 100_000_000)
    record_api._on_event("key_up", 0x45, 0, 0, at + 150_000_000)
    recorder.setArea(0, 0, 400, 80)
    record_api._on_event("mouse_down", 0, 100, 40, at + 300_000_000)  # on the pill: left out
    record_api._on_event("mouse_up", 0, 100, 40, at + 320_000_000)
    recorder.pause()
    assert recorder.paused
    recorder.addWait(2)
    assert recorder.checks == 0 and recorder.count >= 2
    recorder.finish(True)
    assert saved == ["open_bag"] and not recorder.active
    text = (tmp_path / "actions" / "open_bag.py").read_text(encoding="utf-8")
    assert "d.replay(" in text and (tmp_path / "actions" / "open_bag.tape.json").is_file()
    assert recorder.start(tmp_path, "thrown") == ""
    recorder.finish(False)
    assert saved[-1] == "" and not (tmp_path / "actions" / "thrown.py").exists()
    recorder.close()


def test_highlight_finds_the_bots_pictures_on_screen(qt, tmp_path):
    import cv2
    import numpy as np

    from darbit.core.geometry import Region
    from darbit.studio.highlight import Highlight

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "hi-bot"\n', encoding="utf-8")
    rng = np.random.default_rng(3)
    screen = cv2.resize(rng.integers(0, 255, (60, 90, 3), dtype=np.uint8), (900, 600), interpolation=cv2.INTER_CUBIC)
    (tmp_path / "images").mkdir()
    cv2.imwrite(str(tmp_path / "images" / "Lobby.Play.png"), screen[200:260, 300:420])
    stripes = np.zeros((40, 40, 3), np.uint8)
    stripes[:, ::8] = (0, 0, 255)  # not on this screen
    cv2.imwrite(str(tmp_path / "images" / "Lobby.Gone.png"), stripes)
    highlight = Highlight()
    highlight.start(tmp_path, grab=lambda: (screen, Region(0, 0, 900, 600)))
    wait_until(lambda: len(highlight.boxes) == 2)
    boxes = {box["name"]: box for box in highlight.boxes}
    assert boxes["Lobby.Play"]["found"] and (boxes["Lobby.Play"]["x"], boxes["Lobby.Play"]["y"]) == (300, 200)
    assert not boxes["Lobby.Gone"]["found"]
    assert highlight.found == 1 and highlight.isOn
    highlight.stop()
    assert not highlight.isOn and highlight.boxes == []
    highlight.start(tmp_path, grab=lambda: (screen, Region(0, 0, 900, 600)), only="Lobby.Play")
    wait_until(lambda: len(highlight.boxes) == 1)  # only the picture chosen in the Library
    assert highlight.boxes[0]["name"] == "Lobby.Play"
    highlight.stop()


def test_highlight_shows_the_shared_pill_while_it_is_on(qt, tmp_path):
    import cv2
    import numpy as np
    from PySide6.QtCore import QObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.core.geometry import Region
    from darbit.studio.hiding import HidingPill
    from darbit.studio.highlight import Highlight

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "hi-bot"\n', encoding="utf-8")
    (tmp_path / "images").mkdir()
    screen = np.zeros((600, 900, 3), np.uint8)
    screen[200:260, 300:420] = (40, 160, 220)
    cv2.imwrite(str(tmp_path / "images" / "Menu.Start.png"), screen[190:270, 290:430])
    highlight, hiding = Highlight(), HidingPill(watch=lambda moved: None)
    engine = app.load(backend.Studio(FakeClient), highlight=highlight, highlight_hiding=hiding)
    root = engine.rootObjects()[0]
    pill = root.findChild(QQuickWindow, "highlightPill")
    assert not hiding.isOpen and not pill.isVisible()
    highlight.start(tmp_path, grab=lambda: (screen, Region(0, 0, 900, 600)))
    wait_until(lambda: highlight.found == 1)
    assert hiding.isOpen and pill.isVisible()
    wait_until(lambda: pill.findChild(QObject, "highlightFound").property("text").startswith("1 of 1 found"))
    highlight.stop()
    assert not hiding.isOpen and not pill.isVisible()
    del engine


def test_pictures_found_on_the_same_spot_are_look_alikes():
    from darbit.studio.highlight import mark_look_alikes

    boxes = mark_look_alikes(
        [
            {"name": "A", "found": True, "score": 0.99, "x": 10, "y": 10, "w": 50, "h": 40},
            {"name": "B", "found": True, "score": 0.97, "x": 12, "y": 11, "w": 50, "h": 40},
            {"name": "C", "found": True, "score": 0.95, "x": 300, "y": 10, "w": 50, "h": 40},
            {"name": "D", "found": False, "score": 0.2, "needs": 0.7},
        ]
    )
    named = {box["name"]: box for box in boxes}
    assert named["A"]["with"] == ["B"] and named["B"]["with"] == ["A"]
    assert named["A"]["shown"] and not named["B"]["shown"]  # the better one stands for the spot
    assert named["C"]["with"] == [] and named["C"]["shown"]
    assert not named["D"]["shown"]


def test_the_library_keeps_its_columns_when_the_inspector_opens(qt):
    from PySide6.QtQuick import QQuickItem

    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]  # held, or Qt deletes it
    window.resize(1400, 880)
    studio.connect()
    wait_until(lambda: studio.bot.get("name"))
    window.go("library")
    studio.loadLibrary()
    wait_until(lambda: studio.libraryReady)
    page = next(item for item in window.findChildren(QQuickItem) if item.property("roomForInspector") is not None)
    wait_until(lambda: page.property("cardWidth") > 0)
    columns, wide = page.property("columns"), page.property("cardWidth")
    assert (columns - 1) * page.property("gap") + columns * wide > page.width() - 48 - columns  # the row is filled
    page.setProperty("chosen", "Bag.Equip")
    wait_until(lambda: page.property("cardWidth") < wide)  # the cards narrow with the inspector open
    assert page.property("columns") == columns  # but no card moves to another row
    page.setProperty("chosen", "")
    wait_until(lambda: page.property("cardWidth") == wide)
    del engine


def test_the_run_pill_tucks_away_and_only_a_real_move_brings_it_back():
    from darbit.studio.hiding import HIDE_AFTER, Peek

    peek = Peek(left=1000, top=0, width=400, height=80, left_at=0.0)
    assert not peek.time_to_tuck(HIDE_AFTER - 0.1)
    peek.mouse(1200, 40, 1.0)  # on the pill: it stays
    assert not peek.time_to_tuck(10.0)
    peek.mouse(1200, 600, 10.0)  # off it: it waits, then goes
    assert not peek.time_to_tuck(10.0 + HIDE_AFTER - 0.1)
    assert peek.time_to_tuck(10.0 + HIDE_AFTER)
    peek.tucked = True
    assert not peek.mouse(300, 0, 20.0)  # the top edge, but not under the pill
    assert not peek.mouse(1200, 50, 20.0)  # under the pill, but not the edge
    assert peek.mouse(1200, 1, 20.0)
    assert not peek.tucked


class Runs(FakeClient):
    """A bot whose status follows Play and Stop."""

    status = "stopped"

    def call(self, method: str, **params: object) -> object:
        if method == "bot.start":
            self.status = "running"
        if method == "bot.stop":
            self.status = "stopped"
        if method == "bots.list":
            self.asked.append((method, params))
            return [{**BOT, "status": self.status}]
        return super().call(method, **params)


class Window:
    shown = True

    def hide(self):
        self.shown = False

    def show(self):
        self.shown = True

    def raise_(self):
        pass

    def requestActivate(self):
        pass


def test_play_hides_the_studio_behind_the_run_pill_until_the_bot_stops(qt):
    from darbit.studio.hiding import HidingPill

    moves = []
    client = Runs()
    studio = backend.Studio(lambda: client)
    pill = HidingPill(watch=lambda on_move: moves.append(on_move) or (lambda: moves.remove(on_move)))
    window = Window()
    app._connect_run_pill(studio, pill, window)
    studio.connect()
    wait_until(lambda: studio.bot.get("status") == "stopped")
    studio.start()
    wait_until(lambda: studio.bot.get("status") == "running")
    assert pill.isOpen and not window.shown
    assert len(moves) == 1  # real mouse moves are watched while it's open
    studio.stop()
    wait_until(lambda: window.shown)
    assert not pill.isOpen and moves == []
    studio.setRunPill(False)  # off: Play leaves the Studio open
    studio.start()
    wait_until(lambda: studio.bot.get("status") == "running")
    assert window.shown and not pill.isOpen


def test_the_run_pill_draws_without_a_qml_warning(qt):
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.hiding import HidingPill

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        pill = HidingPill(watch=lambda on_move: None)
        studio = backend.Studio(FakeClient)
        engine = app.load(studio, run_pill=pill)
        root = engine.rootObjects()[0]  # held, or Qt deletes it
        studio.connect()
        wait_until(lambda: studio.bot.get("name") == "ad-bot")
        studio.loadOverview()
        wait_until(lambda: len(studio.overview.get("layout", [])) == 8)
        pill.open()
        window = root.findChild(QQuickWindow, "runPill")
        wait_until(window.isVisible)
        assert window.width() < window.screen().size().width() / 2
        pill.close()
        wait_until(lambda: not window.isVisible())
        del engine
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


def test_the_window_opens_where_it_was_left_on_a_screen_still_there():
    from PySide6.QtCore import QRect

    from darbit.studio.window import fit

    screen = QRect(0, 0, 1707, 1000)
    assert fit(None, [screen]) == (None, False)  # the first start: the system picks
    assert fit({"x": 100, "y": 50, "width": 1200, "height": 800}, [screen]) == (QRect(100, 50, 1200, 800), False)
    # bigger than the screen, or hanging off it: made to fit
    assert fit({"x": -6, "y": -6, "width": 1720, "height": 1032, "maximized": True}, [screen]) == (
        QRect(0, 0, 1707, 1000),
        True,
    )
    # on a screen that's gone: the system picks
    assert fit({"x": 3000, "y": 0, "width": 1200, "height": 800}, [screen]) == (None, False)
    assert fit({"x": "a"}, [screen]) == (None, False)


def test_a_second_studio_brings_the_open_one_forward(qt):
    from darbit.studio.window import Door

    name = f"darbit-studio-test-{os.getpid()}"
    assert not Door(name).knock()  # none open
    first = Door(name)
    assert first.open()
    knocks = []
    first.knocked.connect(lambda: knocks.append(1))
    assert Door(name).knock()
    wait_until(lambda: knocks == [1])
    first.close()


def test_closing_keeps_the_studio_in_the_tray_and_its_place(qt):
    from PySide6.QtCore import QRect

    from darbit.server import ui_settings
    from darbit.studio.window import PLACE

    class Tray:
        def isVisible(self):
            return True

        def showMessage(self, *args):
            self.told = args

    class App:
        quits = None

        def setQuitOnLastWindowClosed(self, on):
            self.quits = on

        class aboutToQuit:
            @staticmethod
            def connect(slot):
                pass

    engine = app.load(backend.Studio(FakeClient), place=(QRect(120, 80, 1000, 700), False))
    window = engine.rootObjects()[0]
    assert (window.width(), window.height()) == (1000, 700)
    tray, fake_app = Tray(), App()
    app._keep_in_tray(fake_app, window, tray)
    assert fake_app.quits is False
    window.close()
    wait_until(lambda: ui_settings.get(PLACE) is not None)
    assert ui_settings.get(PLACE)["width"] == 1000
    assert tray.told  # said once where it went
    del engine


def test_the_library_sorts_assets_by_the_kinds_the_service_names():
    from darbit.core.targets import KINDS

    page = (Path(app.__file__).parent / "qml" / "LibraryPage.qml").read_text(encoding="utf-8")
    assert KINDS == ("image", "region", "location")
    for kind in KINDS:
        assert f'key: "{kind}"' in page  # a tab for each kind the service sends


def test_highlight_one_picture_from_the_library(qt):
    client = FakeClient()
    studio = backend.Studio(lambda: client)
    wanted = []
    studio.highlightWanted.connect(lambda folder, name: wanted.append((folder, name)))
    studio.connect()
    wait_until(lambda: studio.bot.get("path"))
    studio.highlightOne("Bag.Equip")
    studio.toggleHighlight()  # Ctrl+Alt+H: the same picture again
    assert wanted == [("/bots/ad-bot", "Bag.Equip"), ("/bots/ad-bot", "Bag.Equip")]


def test_capture_makes_an_image_its_region_and_its_location_together(qt, tmp_path):
    import json

    import numpy as np
    from PySide6.QtCore import Q_ARG, QMetaObject, QObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.capture import Capture, ShotProvider

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
        screen = np.full((400, 600, 3), 30, np.uint8)
        screen[200:240, 300:400] = (90, 200, 90)
        capture = Capture(ShotProvider())
        engine = app.load(backend.Studio(FakeClient), capture)
        capture.start(tmp_path, shot=screen)
        root = engine.rootObjects()[0]
        window = root.findChild(QQuickWindow, "captureWindow")

        def part(name, value):
            QMetaObject.invokeMethod(window, "setPart", Q_ARG("QVariant", name), Q_ARG("QVariant", value))

        part("image", [300, 200, 100, 40])
        part("region", [250, 150, 250, 150])
        part("location", [380, 220])
        assert window.property("kind") == "image"
        QMetaObject.invokeMethod(window, "undo")
        assert window.property("location") is None  # the last change undone
        QMetaObject.invokeMethod(window, "redo")
        assert window.property("location") is not None
        window.findChild(QObject, "nameField").setProperty("text", "Lobby.Play")
        QMetaObject.invokeMethod(window, "save")
        saved = json.loads((tmp_path / "images" / "Lobby.Play.json").read_text(encoding="utf-8"))
        assert saved["kind"] == "image"
        assert saved["region"] == [250, 150, 250, 150]
        assert saved["offset"] == [30, 0]  # from the picture's centre
        # another image searched in a region of the bot's, picked from Saved: shared by name
        part("region", [250, 150, 250, 150])  # a region of its own first, then shared by an image
        window.findChild(QObject, "nameField").setProperty("text", "Lobby.Area")
        QMetaObject.invokeMethod(window, "save")
        part("image", [300, 200, 100, 40])
        QMetaObject.invokeMethod(
            window,
            "useRegion",
            Q_ARG("QVariant", {"name": "Lobby.Area", "region": [250, 150, 250, 150], "used_by": []}),
        )
        assert window.property("regionName") == "Lobby.Area"
        window.findChild(QObject, "nameField").setProperty("text", "Lobby.Other")
        QMetaObject.invokeMethod(window, "save")
        other = json.loads((tmp_path / "images" / "Lobby.Other.json").read_text(encoding="utf-8"))
        assert other["region"] == "Lobby.Area"
        # a retake keeps its region, and its location once the new image is boxed
        QMetaObject.invokeMethod(window, "takeSaved", Q_ARG("QVariant", "Lobby.Play"))
        assert window.property("region") is not None
        part("image", [302, 200, 100, 40])
        point = window.property("location")
        point = point.toVariant() if hasattr(point, "toVariant") else point
        assert [round(value) for value in point] == [382, 220]
        capture.close()
        QtCore.QCoreApplication.processEvents()
        del engine
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


def test_no_qml_property_is_named_like_a_signal_handler():
    import re

    # QML reads `onSomething` as a signal handler, so a property named that way is never bound (the Library's Actions
    # tab stayed empty behind one)
    for page in (Path(app.__file__).parent / "qml").glob("*.qml"):
        found = re.findall(r"property\s+\w+\s+(on[A-Z]\w*)", page.read_text(encoding="utf-8"))
        assert found == [], f"{page.name}: {found}"


def test_a_studio_given_its_own_connection_never_starts_a_service(qt, monkeypatch):
    # a test's or probe's Studio once started a real service in the background each time, and left it running
    monkeypatch.setattr("darbit.service.client.ensure_running", lambda: pytest.fail("started darbit's service"))
    studio = backend.Studio(FakeClient)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")


def test_settings_search_and_flow_into_columns(qt):
    from PySide6.QtCore import Q_ARG, QMetaObject
    from PySide6.QtQuick import QQuickItem

    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    window.resize(1720, 1000)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "settings"))
    wait_until(lambda: studio.settings)
    page = next(item for item in window.findChildren(QQuickItem) if item.property("withHelp") is not None)
    wait_until(lambda: page.property("twoColumns"))
    assert page.property("withHelp")  # wide enough for the help panel too

    def shown():
        found = page.property("shown")
        return found.toVariant() if hasattr(found, "toVariant") else found

    page.setProperty("query", "server")
    wait_until(lambda: [setting["key"] for one in shown() for setting in one["settings"]] == ["modes.server"])
    page.setProperty("query", "nothing like this")
    wait_until(lambda: shown() == [])
    del engine


def test_your_overview_layout_is_kept_per_bot_and_can_go_back(qt):
    studio = backend.Studio(FakeClient)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    studio.loadOverview()
    wait_until(lambda: len(studio.overview.get("layout", [])) == 8)
    mine = studio.overview["layout"][:2]
    studio.saveLayout(mine)
    assert studio.overview["custom"] and len(studio.overview["layout"]) == 2
    again = backend.Studio(FakeClient)
    again.connect()
    wait_until(lambda: again.bot.get("name") == "ad-bot")
    again.loadOverview()
    wait_until(lambda: len(again.overview.get("layout", [])) == 2)  # kept for next time
    again.resetLayout()
    assert not again.overview["custom"] and len(again.overview["layout"]) == 8


def test_customizing_moves_resizes_and_takes_blocks_off(qt):
    from PySide6.QtCore import Q_ARG, QMetaObject

    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    window.resize(1720, 1000)
    wait_until(lambda: len(studio.overview.get("layout", [])) == 8)

    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    page = next(item for item in walk(window.contentItem()) if item.property("galleryOpen") is not None)
    QMetaObject.invokeMethod(page, "resize", Q_ARG("QVariant", 0), Q_ARG("QVariant", 12))
    assert studio.overview["layout"][0]["width"] == 12
    QMetaObject.invokeMethod(page, "remove", Q_ARG("QVariant", 1))
    assert len(studio.overview["layout"]) == 7
    shows = [block["shows"] for block in studio.overview["catalog"] if block["kind"] == "button"]
    QMetaObject.invokeMethod(
        page,
        "add",
        Q_ARG("QVariant", {"kind": "button", "shows": shows[0], "title": "dim_run", "width": 4, "origin": "ad-bot"}),
    )
    assert studio.overview["layout"][-1]["shows"] == "action:dim_run"
    del engine


def test_a_retake_opens_capture_named_and_on_its_kind(qt, tmp_path):
    import cv2
    import numpy as np
    from PySide6.QtCore import QObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.capture import Capture, ShotProvider

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    (tmp_path / "images").mkdir()
    cv2.imwrite(str(tmp_path / "images" / "Lobby.Play.png"), np.zeros((8, 8, 3), np.uint8))  # taken already
    (tmp_path / "images" / "Lobby.Play.json").write_text("{}", encoding="utf-8")  # a retake still names it
    capture = Capture(ShotProvider())
    engine = app.load(backend.Studio(FakeClient), capture)
    root = engine.rootObjects()[0]
    window = root.findChild(QQuickWindow, "captureWindow")
    for kind in ("image", "region", "location"):
        capture.start(tmp_path, "one", "Lobby.Play", kind, shot=np.zeros((300, 400, 3), np.uint8))
        wait_until(lambda: window.findChild(QObject, "nameField").property("text") == "Lobby.Play")
        assert window.property("tool") == kind
        capture.close()
        QtCore.QCoreApplication.processEvents()
    del engine


def test_a_retake_on_a_failures_screenshot_opens_capture_on_the_main_screen_of_it(qt, tmp_path, monkeypatch):
    import cv2
    import numpy as np

    from darbit.capture import service as capture_service
    from darbit.core.geometry import Region
    from darbit.studio import capture as studio_capture

    # two screens side by side, the main one on the right: the screenshot is the whole desktop
    monkeypatch.setattr(studio_capture.screen, "desktop", lambda: Region(-400, 0, 800, 300))
    monkeypatch.setattr(studio_capture.screen, "monitors", lambda: [Region(0, 0, 400, 300), Region(-400, 0, 400, 300)])
    shot = np.zeros((300, 800, 3), np.uint8)
    shot[:, 400:] = 255  # the main screen's half
    path = tmp_path / "failed.png"
    cv2.imwrite(str(path), shot)
    pixels, origin = studio_capture.shot_of_failure(path)
    assert pixels.shape == (300, 400, 3) and pixels.min() == 255
    assert origin == Region(0, 0, 400, 300)
    monkeypatch.setattr(studio_capture.screen, "desktop", lambda: Region(0, 0, 400, 300))
    assert studio_capture.shot_of_failure(path) is None  # the screens are laid out differently now
    assert studio_capture.shot_of_failure(tmp_path / "gone.jpg") is None
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "fish-bot"\n', encoding="utf-8")
    capture = studio_capture.Capture(studio_capture.ShotProvider())
    capture.start(tmp_path, "one", "Rod.Cast", "image", shot=pixels, origin=Region(-400, 0, 400, 300))
    assert capture_service._current().origin == Region(-400, 0, 400, 300)  # saved boxes sit where that screen was
    capture.close()

    studio = backend.Studio(FakeClient)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    wanted = []
    studio.captureOnShotWanted.connect(lambda *args: wanted.append(args))
    studio.retakeOn("Rod.Cast", "image", path.as_uri())
    assert wanted == [("/bots/ad-bot", "Rod.Cast", "image", str(path).replace("\\", "/"))]


def test_the_bot_started_anywhere_hides_the_studio_but_one_already_running_doesnt(qt):
    from darbit.studio.hiding import HidingPill

    client = Runs()
    studio = backend.Studio(lambda: client)
    pill = HidingPill(watch=lambda on_move: lambda: None)
    window = Window()
    app._connect_run_pill(studio, pill, window)
    studio.connect()
    wait_until(lambda: studio.bot.get("status") == "stopped")
    client.status = "running"  # started from the command line, the tray or a schedule: not the Studio's Play
    studio._on_event("project.status", {"path": BOT["path"], "status": "running"})
    wait_until(lambda: pill.isOpen)
    assert not window.shown

    already = Runs()
    already.status = "running"
    other = backend.Studio(lambda: already)
    other_pill = HidingPill(watch=lambda on_move: lambda: None)
    other_window = Window()
    app._connect_run_pill(other, other_pill, other_window)
    other.connect()
    wait_until(lambda: other.bot.get("status") == "running")
    assert other_window.shown and not other_pill.isOpen  # opening the Studio on a running bot shows it


def test_typing_a_known_name_after_boxing_brings_its_region_and_location_back(qt, tmp_path):
    import json

    import numpy as np
    from PySide6.QtCore import Q_ARG, QMetaObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.capture import Capture, ShotProvider

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "Bag.Menu.json").write_text(json.dumps({"kind": "region", "region": [10, 10, 300, 200]}))
    (tmp_path / "images" / "Bag.Equip.json").write_text(
        json.dumps({"kind": "image", "region": "Bag.Menu", "offset": [5, 0]})
    )
    capture = Capture(ShotProvider())
    engine = app.load(backend.Studio(FakeClient), capture)
    root = engine.rootObjects()[0]
    window = root.findChild(QQuickWindow, "captureWindow")
    capture.start(tmp_path, shot=np.zeros((300, 400, 3), np.uint8))
    QMetaObject.invokeMethod(window, "setPart", Q_ARG("QVariant", "image"), Q_ARG("QVariant", [50, 50, 40, 20]))
    QMetaObject.invokeMethod(window, "takeSaved", Q_ARG("QVariant", "Bag.Equip"))  # the name, typed afterwards

    def value(name):
        found = window.property(name)
        return found.toVariant() if hasattr(found, "toVariant") else found

    assert value("region") == [10, 10, 300, 200] and window.property("regionName") == "Bag.Menu"
    assert [round(part) for part in value("location")] == [75, 60]  # its centre, moved by its saved offset
    capture.close()
    del engine


def test_an_image_is_searched_on_the_screen_in_a_shared_region_or_its_own_and_saving_closes(qt, tmp_path):
    import json

    import numpy as np
    from PySide6.QtCore import Q_ARG, QMetaObject, QObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.capture import Capture, ShotProvider

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    capture = Capture(ShotProvider())
    engine = app.load(backend.Studio(FakeClient), capture)
    root = engine.rootObjects()[0]
    window = root.findChild(QQuickWindow, "captureWindow")
    capture.start(tmp_path, shot=np.zeros((300, 400, 3), np.uint8))

    def call(name, *values):
        QMetaObject.invokeMethod(window, name, *[Q_ARG("QVariant", value) for value in values])

    call("setPart", "image", [50, 50, 40, 20])
    assert window.property("searchIn") == "screen"
    call("setPart", "region", [10, 10, 300, 200])
    assert window.property("searchIn") == "own"
    call("shareRegion", "Bag.Menu")  # the drawn region becomes a shared one, and the image names it
    assert window.property("searchIn") == "shared"
    assert json.loads((tmp_path / "images" / "Bag.Menu.json").read_text(encoding="utf-8"))["kind"] == "region"
    call("searchOn", "own")
    assert window.property("searchIn") == "own"  # its own copy now
    call("searchOn", "screen")
    assert window.property("searchIn") == "screen"
    call("searchOn", "shared")
    window.findChild(QObject, "nameField").setProperty("text", "Bag.Equip")
    call("useRegion", {"name": "Bag.Menu", "region": [10, 10, 300, 200], "used_by": []})
    call("save")
    saved = json.loads((tmp_path / "images" / "Bag.Equip.json").read_text(encoding="utf-8"))
    assert saved["region"] == "Bag.Menu"
    wait_until(lambda: not capture.isOpen)  # nothing left to take: it closes by itself
    del engine


def test_the_studio_keeps_one_look():
    import re

    # a control drawn by hand is how the pages drift apart: the shared ones are in docs/style/ui/design-system.md
    shared_in = {"TextField": "Field", "Switch": "Switcher", "ComboBox": "Dropdown", "Slider": "ValueSlider"}
    sheets = {"NewBotSheet", "RecordSheet"}  # whole sheets, not menus
    for page in (Path(app.__file__).parent / "qml").glob("*.qml"):
        source = page.read_text(encoding="utf-8")
        for control, home in shared_in.items():
            if page.stem != home:
                assert not re.search(rf"\b{control} \{{", source), f"{page.name} draws its own {control}: use {home}"
        if page.stem != "MenuPanel" and page.stem not in sheets:
            assert not re.search(r"\bPopup \{", source), f"{page.name} draws its own menu: use MenuPanel"
        assert "glassStrong" not in source, f"{page.name}: panels use colors.solid"


def test_a_theme_has_a_solid_panel_and_the_kinds_colours():
    colors = theme.colors("glass-dark")
    assert colors["solid"].startswith("#ff") and colors["solid"][3:] == colors["glassStrong"][3:]
    assert colors["kindRegion"] == colors["accent2"]


def test_the_doctors_checks_are_asked_for_the_shown_bot(qt):
    client = FakeClient()
    studio = backend.Studio(lambda: client)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    studio.checkBot()
    wait_until(lambda: studio.checks.get("problems") == 1)
    assert ("bot.doctor", {"bot": "/bots/ad-bot"}) in client.asked
    assert studio.checks["bot"] == "/bots/ad-bot"  # whose checks they are, if another bot is shown by then
    assert studio.checks["checks"][1]["name"] == "game window"


def test_the_action_editor_sets_breakpoints_and_steps(qt):

    client = FakeClient()
    studio = backend.Studio(lambda: client)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    QMetaObject.invokeMethod(window, "openAction", Q_ARG("QVariant", "dim_run"))
    wait_until(lambda: studio.action.get("name") == "dim_run")

    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    page = next(item for item in walk(window.contentItem()) if item.property("pausedHere") is not None)
    QMetaObject.invokeMethod(page, "toggleStop", Q_ARG("QVariant", 9))
    wait_until(
        lambda: ("bot.action.breakpoints", {"bot": "/bots/ad-bot", "name": "dim_run", "lines": [9]}) in client.asked
    )
    assert studio.action["breakpoints"] == [9]
    QMetaObject.invokeMethod(page, "toggleStop", Q_ARG("QVariant", 9))
    assert studio.action["breakpoints"] == []
    studio.stepThroughAction("dim_run")
    wait_until(
        lambda: ("bot.action.play", {"bot": "/bots/ad-bot", "name": "dim_run", "stepping": True}) in client.asked
    )
    studio._on_event("action.paused", {"action": "dim_run", "line": 6})
    assert page.property("pausedHere")
    studio.stepAction()
    studio.resumeAction()
    wait_until(lambda: ("bot.action.resume", {"bot": "/bots/ad-bot"}) in client.asked)
    assert ("bot.action.step", {"bot": "/bots/ad-bot"}) in client.asked
    del engine


def test_the_library_shows_targets_where_they_sit_on_their_screen(qt):

    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    window.resize(1400, 880)
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "library"))

    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    page = next(item for item in walk(window.contentItem()) if item.property("roomForInspector") is not None)
    page.setProperty("showScreens", True)
    wait_until(lambda: len(studio.screens) == 1)
    view = next(item for item in walk(window.contentItem()) if item.metaObject().className().startswith("ScreenView"))
    wait_until(lambda: view.property("names") is not None)
    QMetaObject.invokeMethod(view, "picked", Q_ARG("QString", "Bag.Equip"), Q_ARG("QString", "image"))
    wait_until(lambda: page.property("chosen") == "Bag.Equip")
    assert not page.property("chosenIsAction")
    del engine


def test_keys_change_in_darbit_settings_and_refuse_one_taken(qt):
    from darbit import keymap

    studio = backend.Studio(FakeClient)
    assert studio.keys["palette.open"] == "ctrl+k"
    told = []
    studio.keysChanged.connect(lambda: told.append(studio.keys["palette.open"]))
    studio.setKey("palette.open", "ctrl+j")
    assert told == ["ctrl+j"] and keymap.combo("palette.open") == "ctrl+j"
    studio.setKey("search", "ctrl+j")  # taken: refused, and it says by what
    assert keymap.combo("search") == "ctrl+f" and "Command palette" in studio.message
    studio.setKey("search", "")  # off
    assert keymap.combo("search") == ""
    studio.resetKey("palette.open")
    studio.resetKey("search")
    assert studio.keys["palette.open"] == "ctrl+k" and studio.keys["search"] == "ctrl+f"
    row = next(row for row in studio.keyRows if row["action"] == "capture.freeze")
    assert row["keys"] == row["default"] == "ctrl+alt+c"


def test_the_command_palette_finds_and_runs_commands(qt):
    from PySide6.QtCore import QObject

    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    window.resize(1400, 880)
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    palette = window.findChild(QObject, "commandPalette")
    QMetaObject.invokeMethod(palette, "open")
    wait_until(lambda: palette.property("visible"))
    search = window.findChild(QObject, "paletteSearch")
    search.setProperty("text", "results")

    def labels():
        found = palette.property("shown")
        found = found.toVariant() if hasattr(found, "toVariant") else found
        return [one["label"] for one in found]

    wait_until(lambda: labels() == ["Results"])
    QMetaObject.invokeMethod(palette, "runAt", Q_ARG("QVariant", 0))
    wait_until(lambda: window.property("page") == "results")
    del engine


def test_edit_opens_the_bots_folder_in_vs_code_or_the_explorer(qt, monkeypatch):
    studio = backend.Studio(FakeClient)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    started = []
    opened = []
    monkeypatch.setattr(backend.subprocess, "Popen", lambda command, **options: started.append(command))
    monkeypatch.setattr(backend.QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()))
    monkeypatch.setattr(backend.shutil, "which", lambda name: "C:/code.cmd")
    studio.editBot()
    assert started == [["C:/code.cmd", "/bots/ad-bot"]]
    monkeypatch.setattr(backend.shutil, "which", lambda name: None)
    studio.editBot()
    assert opened == ["/bots/ad-bot"]


def test_an_image_that_may_have_stopped_matching_shows_and_is_told_once(qt, monkeypatch):
    from PySide6.QtCore import QObject

    answer = _overview_answer()
    failing = {
        "target": "Team.Card",
        "since": "2026-11-06T01:15:08.977",
        "count": 2,
        "sentence": "AFK failed 2 times in a row waiting for it (closest 0.60 of the 0.85 it needs).",
    }
    answer["data"] = {**answer["data"], "failing": failing}
    monkeypatch.setitem(ANSWERS, "bot.overview", answer)
    studio = backend.Studio(FakeClient)
    told = []
    studio.pictureFailing.connect(lambda title, text: told.append(title))
    engine = app.load(studio)
    root = engine.rootObjects()[0]
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    studio.loadOverview()
    banner = root.findChild(QObject, "failingBanner")
    wait_until(lambda: banner.property("visible"))
    assert banner.property("title").startswith("Team.Card may have stopped matching")
    studio.loadOverview()
    wait_until(lambda: len(told) >= 1)
    QtCore.QCoreApplication.processEvents()
    assert told == ["ad-bot: Team.Card may have stopped matching"]  # once, however often the Overview comes
    del engine


@pytest.mark.parametrize(
    ("recoveries", "said"),
    [
        (None, ["3", "times today", "mostly disconnected (2 of 3)", "last 11:15 · rejoin: disconnected"]),
        (
            {"count": 0, "reason": "", "reason_count": 0, "last": None, "hows": []},
            ["None", "today", "It hasn't had to recover today."],
        ),
    ],
)
def test_the_recoveries_block_says_how_often_and_why(qt, monkeypatch, recoveries, said):
    answer = _overview_answer()
    if recoveries is not None:
        answer["data"]["recoveries"] = recoveries
    monkeypatch.setitem(ANSWERS, "bot.overview", answer)
    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    wait_until(lambda: len(studio.overview.get("layout", [])) == 8)

    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    def texts():
        found = []
        for item in walk(window.contentItem()):
            if item.property("title") == "Recoveries" and item.property("kind") == "recoveries":
                found = [child.property("text") for child in walk(item) if child.property("text")]
        return found

    wait_until(lambda: all(line in texts() for line in said))
    del engine


def _failure(tmp_path, screenshot=True, target="Lobby.Play"):
    """A problem on the Results page as server/problems.py says it: the image it waited for, its closest match on the
    screenshot it was seen on, and the steps before it."""
    import cv2
    import numpy as np

    cv2.imwrite(str(tmp_path / "Lobby.Play.png"), np.full((40, 100, 3), 200, np.uint8))
    cv2.imwrite(str(tmp_path / "shot.jpg"), np.zeros((900, 1600, 3), np.uint8))
    shot = (tmp_path / "shot.jpg").as_uri() if screenshot else None
    search = {"target": target, "seconds": 120, "closest": 0.62, "needs": 0.85, "at": [700, 430]}
    search |= {"picture": (tmp_path / "Lobby.Play.png").as_uri(), "screenshot": shot}
    before = [
        {
            "time": "2026-10-31T11:57:58.000",
            "kind": "click",
            "what": "Lobby.Join",
            "ok": False,
            "say": "click Lobby.Join: not found",
        },
    ]
    return {
        "cause": "changed",
        "label": "An image looks different now",
        "tone": "danger",
        "act": True,
        "step": "Rejoin",
        "path": "Rejoin",
        "reason": "Lobby.Play didn't show",
        "sentence": "It couldn't find Lobby.Play for 2 minutes.",
        "target": target,
        "count": 1,
        "times": ["2026-10-31T12:00:04.000"],
        "screenshot": shot,
        "screenshots": [shot] if shot else [],
        "searches": [search] if target else [],
        "before": before,
    }


def _results_page(monkeypatch, problem):
    from darbit.core.geometry import Region
    from darbit.platform import screen

    monkeypatch.setattr(screen, "desktop", lambda: Region(-400, 0, 2000, 900))  # a screen left of the main one
    monkeypatch.setitem(ANSWERS, "bot.day", {**ANSWERS["bot.day"], "problems": [problem]})
    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    window.resize(1400, 1000)
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "results"))

    def find(name):
        def walk(item):
            yield item
            for child in item.childItems():
                yield from walk(child)

        for item in walk(window.contentItem()):
            if item.objectName() == name:
                return item
        return None

    wait_until(lambda: find("retakeNow") is not None and find("retakeNow").isVisible())
    return studio, engine, find


def test_a_failure_shows_its_closest_match_and_retakes_on_its_screen(qt, tmp_path, monkeypatch):
    studio, engine, find = _results_page(monkeypatch, _failure(tmp_path))
    match = find("closestMatch")
    wait_until(match.isVisible)
    shot = match.parentItem()
    scale = (shot.width() - 2) / 1600  # the screenshot fills the frame's width
    top = 1 + (shot.height() - 2 - 900 * scale) / 2
    assert abs(match.x() - (1 + 1100 * scale)) < 1  # 700 on screen is 1100 into a desktop starting at -400
    assert abs(match.y() - (top + 430 * scale)) < 1
    assert abs(match.width() - 100 * scale) < 1  # as big as the image it waited for
    on_shot, now = [], []
    studio.captureOnShotWanted.connect(lambda *args: on_shot.append(args))
    studio.captureWanted.connect(lambda *args: now.append(args))
    QMetaObject.invokeMethod(find("retakeOnShot"), "clicked")
    QMetaObject.invokeMethod(find("retakeNow"), "clicked")
    assert on_shot == [("/bots/ad-bot", "Lobby.Play", "image", str(tmp_path / "shot.jpg").replace("\\", "/"))]
    assert now == [("/bots/ad-bot", "one", "Lobby.Play", "image")]
    del engine


def test_a_failure_without_a_screenshot_retakes_on_the_screen_now(qt, tmp_path, monkeypatch):
    _studio, engine, find = _results_page(monkeypatch, _failure(tmp_path, screenshot=False))
    assert not find("retakeOnShot").isVisible()
    assert not find("closestMatch").isVisible()
    assert find("retakeNow").property("text") == "Retake Lobby.Play on the screen now"
    del engine


def test_a_failure_with_no_image_waited_for_has_no_retake(qt, tmp_path, monkeypatch):
    problem = _failure(tmp_path, target="")
    problem["act"] = True
    monkeypatch.setitem(ANSWERS, "bot.day", {**ANSWERS["bot.day"], "problems": [problem]})
    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "results"))
    wait_until(lambda: studio.day.get("problems"))
    QtCore.QCoreApplication.processEvents()

    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    texts = []
    wait_until(
        lambda: (
            "Nothing it looked for ran out before it stopped."
            in [i.property("text") for i in walk(window.contentItem())]
        )
    )
    for item in walk(window.contentItem()):
        if item.objectName() in ("retakeNow", "retakeOnShot"):
            texts.append(item.isVisible())
    assert texts and not any(texts)
    del engine


def test_the_magnifier_follows_the_mouse_after_a_click_and_ctrl_wheel_zooms_it(qt, tmp_path):
    import numpy as np
    from PySide6.QtCore import QObject, QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest

    from darbit.studio.capture import Capture, ShotProvider

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    capture = Capture(ShotProvider())
    engine = app.load(backend.Studio(FakeClient), capture)
    root = engine.rootObjects()[0]
    window = root.findChild(QQuickWindow, "captureWindow")
    capture.start(tmp_path, shot=np.zeros((600, 800, 3), np.uint8))
    wait_until(window.isVisible)
    window.resize(800, 600)
    QtCore.QCoreApplication.processEvents()
    magnifier = window.findChild(QObject, "magnifier")

    def under_mouse():
        at = magnifier.property("at")
        return (round(at.x()), round(at.y()))

    QTest.mouseMove(window, QPoint(200, 300))
    wait_until(lambda: under_mouse() == (200, 300))
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(200, 300))
    QTest.mouseMove(window, QPoint(420, 350))
    wait_until(lambda: under_mouse() == (420, 350))  # it still follows the mouse
    QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPoint(420, 350))
    QTest.mouseMove(window, QPoint(500, 420))
    wait_until(lambda: under_mouse() == (500, 420))  # and while a box is drawn
    QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPoint(500, 420))
    zoom = magnifier.property("zoom")
    at = QPointF(500, 420)
    wheel = QWheelEvent(
        at, window.mapToGlobal(at), QPoint(), QPoint(0, 120), Qt.NoButton, Qt.ControlModifier, Qt.NoScrollPhase, False
    )
    QtCore.QCoreApplication.sendEvent(window, wheel)
    wait_until(lambda: magnifier.property("zoom") > zoom)  # Ctrl+wheel: closer
    capture.close()
    del engine
