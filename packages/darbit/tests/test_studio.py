"""darbit Studio: its theme tokens, what its pages bind to, and every page drawn offscreen with no QML warning.

Needs the studio extra (PySide6); skipped without it. The service is a fake client with canned answers.
"""

import json
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
        {"name": "darbit.toml", "ok": True, "found": "ad-bot 1.0.0", "fix": "", "missing": []},
        {"name": "game window", "ok": False, "found": "no window called Game", "fix": "open it first", "missing": []},
    ],
    "problems": 1,
}
ANSWERS["bot.library.screens"] = [
    {
        "screen": "Bag",
        "picture": "",
        "shot": "C:/bots/ad-bot/screens/Bag.jpg",
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
    # still windows: with effects off every Behavior and animation lands at once, so a test reads where things end
    # up, not where an animation happens to be; and no pill slides away on the clock while a slow run goes on
    _keep_effects(tmp_path, False)
    monkeypatch.setattr("darbit.studio.hiding.HIDE_AFTER", float("inf"))
    return QGuiApplication.instance() or QGuiApplication(["test"])


@pytest.fixture
def effects(qt, tmp_path):
    """The windows with their motion and glass on, for the tests that only check they draw without a warning."""
    _keep_effects(tmp_path, True)
    return qt


def _keep_effects(tmp_path, on):
    config = tmp_path / "config"
    config.mkdir(exist_ok=True)
    (config / "ui.json").write_text(json.dumps({"studio.effects": on}), encoding="utf-8")


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


class Changing(FakeClient):
    """The service, also answering the Library's deletes, renames and undo."""

    def call(self, method, **params):
        if method.startswith("bot.library.") and method != "bot.library":
            self.asked.append((method, params))
            return {}
        return super().call(method, **params)


def test_a_delete_or_rename_in_the_library_is_taken_back_from_the_toast(qt):
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtQuick import QQuickItem
    from PySide6.QtTest import QTest

    client = Changing()
    studio = backend.Studio(lambda: client)
    engine = app.load(studio)
    root = engine.rootObjects()[0]
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    undo = root.findChild(QQuickItem, "toastUndo")
    assert not undo.isVisible()
    studio.deleteAsset("Bag.Equip")
    wait_until(lambda: undo.isVisible())  # "Deleted Bag.Equip", with Undo
    studio.selectBot("/bots/other")  # taken back on the bot it was done to, even with another shown
    root.grabWindow()  # a frame: the toast's row lays out its parts
    middle = undo.mapToScene(QPointF(undo.width() / 2, undo.height() / 2)).toPoint()
    QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier, middle)  # on Undo, not the toast under it
    wait_until(lambda: ("bot.library.undelete", {"bot": "/bots/ad-bot"}) in client.asked)
    assert not undo.isVisible()
    studio.selectBot("/bots/ad-bot")
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    undone = []
    studio.undone.connect(lambda was, now: undone.append((was, now)))
    studio.renameAsset("Bag.Equip", "Bag.Wear")
    wait_until(lambda: undo.isVisible())
    studio.undoLast()
    back = ("bot.library.rename", {"bot": "/bots/ad-bot", "name": "Bag.Wear", "to": "Bag.Equip"})
    wait_until(lambda: back in client.asked)
    wait_until(lambda: ("Bag.Wear", "Bag.Equip") in undone)  # the inspector follows it back
    studio.renameAction("dim_run", "dim_go")  # actions too, through their own requests
    wait_until(lambda: studio._undo is not None and studio._undo.method == "bot.action.rename")
    studio.undoLast()
    wait_until(
        lambda: ("bot.action.rename", {"bot": "/bots/ad-bot", "name": "dim_go", "to": "dim_run"}) in client.asked
    )
    studio.undoLast()  # once only
    del engine


@pytest.mark.parametrize("theme_name", ["glass-dark", "high-contrast"])
@pytest.mark.parametrize("page", ["overview", "library", "results", "settings", "studio", "action"])
def test_every_page_draws_without_a_qml_warning(effects, tmp_path, page, theme_name):
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


def test_the_ghost_cursor_draws_without_a_qml_warning(effects, tmp_path):
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


def test_the_first_overview_welcomes_without_a_qml_warning(effects, tmp_path):
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


class Empty(FakeClient):
    """A bot that has nothing yet: no Images, Regions, Locations or Actions, and no run ever."""

    def call(self, method: str, **params: object) -> object:
        if method in ("bot.library", "bot.actions", "bot.days"):
            return []
        if method == "bot.overview":
            return {**ANSWERS["bot.overview"], "ran": False}
        return super().call(method, **params)


def test_every_empty_page_says_why_and_offers_the_main_action_with_its_key(qt):
    from PySide6.QtQuick import QQuickItem

    client = Empty()
    studio = backend.Studio(lambda: client)
    engine = app.load(studio)
    window = engine.rootObjects()[0]  # held, or Qt deletes it
    window.resize(1400, 880)
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    studio.selectBot("/bots/other")  # stopped: Start is offered
    wait_until(lambda: studio.bot.get("name") == "other")

    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "overview"))
    wait_until(lambda: _named(window, "overviewEmpty") is not None and _named(window, "overviewEmpty").isVisible())
    empty = _named(window, "overviewEmpty")
    assert (empty.property("title"), empty.property("action"), empty.property("keys")) == ("No runs yet", "Start", "F5")

    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "library"))
    wait_until(lambda: studio.libraryReady)
    page = next(item for item in window.findChildren(QQuickItem) if item.property("roomForInspector") is not None)
    empty = _named(window, "libraryEmpty")
    said = {}
    for tab in ("all", "image", "region", "location", "action"):
        page.setProperty("kind", tab)
        said[tab] = (empty.property("title"), empty.property("action"), empty.property("keys"))
    assert said == {
        "all": ("Nothing in the Library yet", "Capture", "Ctrl+Alt+C"),
        "image": ("No Images yet", "Capture", "Ctrl+Alt+C"),
        "region": ("No Regions yet", "Capture", "Ctrl+Alt+C"),
        "location": ("No Locations yet", "Capture", "Ctrl+Alt+C"),
        "action": ("No Actions yet", "Record", ""),  # the record key only finishes a recording
    }
    wanted = []
    studio.captureWanted.connect(lambda *args: wanted.append(args))
    page.setProperty("kind", "image")
    QMetaObject.invokeMethod(empty, "acted")
    assert wanted == [("/bots/other", "any", "", "image")]

    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "results"))
    wait_until(lambda: _named(window, "resultsEmpty") is not None and _named(window, "resultsEmpty").isVisible())
    assert _named(window, "resultsEmpty").property("title") == "No runs yet"
    del engine


def test_results_with_no_run_today_link_to_the_last_day_with_runs(qt):
    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "results"))
    wait_until(lambda: _named(window, "todayEmpty") is not None and _named(window, "todayEmpty").isVisible())
    today = _named(window, "todayEmpty")
    assert today.property("title") == "No runs today"
    assert today.property("link") and today.property("action").startswith("See ")
    assert today.property("action") != "See yesterday"  # the only day with runs is long ago: its date
    QMetaObject.invokeMethod(today, "acted")
    wait_until(lambda: studio.day.get("day") == "2026-10-31")
    wait_until(lambda: not today.isVisible())
    del engine


class LongNames(FakeClient):
    """The service, with a bot and a gain whose names are too long for their places."""

    bot = "the-weekend-raid-and-daily-farming-bot-with-a-long-name"
    gain = "Gems from the weekend raids and the daily login rewards together"

    def call(self, method, **params):
        answer = super().call(method, **params)
        if method == "bots.list":
            return [{**answer[0], "name": self.bot}] + answer[1:]
        if method == "bot.day":
            return {**answer, "gains": [{**answer["gains"][0], "name": self.gain}]}
        return answer


@pytest.mark.parametrize("sidebar", [True, False])
def test_a_name_too_long_for_the_bar_or_a_gain_row_ends_in_an_ellipsis_and_shows_whole_on_hover(qt, sidebar):
    studio = backend.Studio(LongNames)
    studio.setSidebar(sidebar)
    engine = app.load(studio)
    window = engine.rootObjects()[0]
    window.resize(1100, 700)
    wait_until(lambda: studio.bot.get("name") == LongNames.bot)
    QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "results"))
    studio.loadDay("2026-10-31")
    wait_until(lambda: _named(window, "gainName") is not None)
    bot = _named(window, "barName" if sidebar else "pickerName")
    gain = _named(window, "gainName")
    wait_until(lambda: bot.property("truncated") and gain.property("truncated"))  # drawn with "…"
    assert (bot.property("text"), gain.property("text")) == (LongNames.bot, LongNames.gain)  # whole in the tooltip
    del engine


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
    assert capture.save("", "image", box, None, None)["error"] == "Give it a name first, by its box"
    capture.close()
    assert not capture.isOpen


def test_the_capture_window_draws_a_box_and_matches_without_a_qml_warning(effects, tmp_path):
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
        capture.start(tmp_path, shot=screen, several=False)  # one target: Test checks just it
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


def test_captures_pill_works_by_keyboard_from_the_name(qt, tmp_path):
    import numpy as np
    from PySide6.QtCore import Qt
    from PySide6.QtQuick import QQuickItem, QQuickWindow
    from PySide6.QtTest import QTest

    from darbit.studio.capture import Capture, ShotProvider

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    screen = np.full((400, 600, 3), 30, np.uint8)
    screen[200:240, 300:400] = (90, 200, 90)
    capture = Capture(ShotProvider())
    engine = app.load(backend.Studio(FakeClient), capture)
    capture.start(tmp_path, shot=screen, several=False)
    root = engine.rootObjects()[0]
    window = root.findChild(QQuickWindow, "captureWindow")
    scale = window.property("scale")
    QMetaObject.invokeMethod(
        window, "clicked", Q_ARG("QVariant", 350 * scale), Q_ARG("QVariant", 220 * scale), Q_ARG("QVariant", True)
    )
    name = window.findChild(QQuickItem, "nameField")
    name.setProperty("text", "Menu.Play")
    name.forceActiveFocus()
    QTest.keyClick(window, Qt.Key_Tab)  # from the name into the pill, not the next kind
    assert window.property("tool") == "image"
    assert window.activeFocusItem() is not name
    seen = []
    while window.activeFocusItem().objectName() != "saveButton" and len(seen) < 12:
        seen.append(window.activeFocusItem())
        QTest.keyClick(window, Qt.Key_Tab)
    assert window.activeFocusItem().objectName() == "saveButton"
    QTest.keyClick(window, Qt.Key_Backtab)  # back one, and on again
    assert window.activeFocusItem() is seen[-1]
    QTest.keyClick(window, Qt.Key_Tab)
    QTest.keyClick(window, Qt.Key_Tab)  # past Save: round to the name
    assert window.activeFocusItem() is name
    QTest.keyClick(window, Qt.Key_Backtab)  # and back from the name to Save
    assert window.activeFocusItem().objectName() == "saveButton"
    assert window.property("tool") == "image"  # Tab never fell through to the next kind
    QTest.keyClick(window, Qt.Key_Escape)  # back to the shot, nothing dropped
    assert window.activeFocusItem().objectName() == "stage"
    assert window.property("image") is not None
    name.forceActiveFocus()
    QTest.keyClick(window, Qt.Key_Tab)
    while window.activeFocusItem().objectName() != "saveButton":
        QTest.keyClick(window, Qt.Key_Tab)
    QTest.keyClick(window, Qt.Key_Return)  # Enter on Save saves
    wait_until(lambda: (tmp_path / "images" / "Menu.Play.png").is_file())
    capture.close()
    QtCore.QCoreApplication.processEvents()
    del engine


def test_captures_kinds_and_where_an_image_is_searched_are_tab_stops(qt, tmp_path):
    import numpy as np
    from PySide6.QtCore import Qt
    from PySide6.QtQuick import QQuickItem, QQuickWindow
    from PySide6.QtTest import QTest

    from darbit.studio.capture import Capture, ShotProvider

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    capture = Capture(ShotProvider())
    engine = app.load(backend.Studio(FakeClient), capture)
    capture.start(tmp_path, shot=np.zeros((300, 400, 3), np.uint8), several=False)
    root = engine.rootObjects()[0]
    window = root.findChild(QQuickWindow, "captureWindow")

    def call(name, *values):
        QMetaObject.invokeMethod(window, name, *[Q_ARG("QVariant", value) for value in values])

    def focused():
        return window.activeFocusItem().property("key")

    def press(key):
        QTest.keyClick(window, key)
        return focused()

    call("setPart", "image", [50, 50, 40, 20])
    call("setPart", "region", [10, 10, 300, 200])
    call("choose", "image")
    name = window.findChild(QQuickItem, "nameField")
    name.forceActiveFocus()
    assert [press(Qt.Key_Tab), press(Qt.Key_Tab), press(Qt.Key_Tab)] == ["image", "region", "location"]
    assert window.activeFocusItem().property("lit")  # with the focus it looks as it does hovered
    assert press(Qt.Key_Backtab) == "region"
    assert press(Qt.Key_Space) == "region"  # picked, and the focus stays for the next Tab
    assert window.property("tool") == "region"
    assert window.property("searchIn") == "own"
    # where the image is searched shows with Region picked, and comes next
    assert [press(Qt.Key_Tab), press(Qt.Key_Tab), press(Qt.Key_Tab)] == ["location", "screen", "shared"]
    assert press(Qt.Key_Backtab) == "screen"
    assert press(Qt.Key_Return) == "screen"
    assert window.property("searchIn") == "screen"  # searched on the whole screen now
    assert window.property("tool") == "region"
    QTest.keyClick(window, Qt.Key_Escape)  # back to the shot
    assert window.activeFocusItem().objectName() == "stage"
    capture.close()
    QtCore.QCoreApplication.processEvents()
    del engine


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


def test_scout_finds_the_bots_images_on_screen(qt, tmp_path):
    import cv2
    import numpy as np

    from darbit.core.geometry import Region
    from darbit.studio.scout import Scout

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "hi-bot"\n', encoding="utf-8")
    rng = np.random.default_rng(3)
    screen = cv2.resize(rng.integers(0, 255, (60, 90, 3), dtype=np.uint8), (900, 600), interpolation=cv2.INTER_CUBIC)
    (tmp_path / "images").mkdir()
    cv2.imwrite(str(tmp_path / "images" / "Lobby.Play.png"), screen[200:260, 300:420])
    stripes = np.zeros((40, 40, 3), np.uint8)
    stripes[:, ::8] = (0, 0, 255)  # not on this screen
    cv2.imwrite(str(tmp_path / "images" / "Lobby.Gone.png"), stripes)
    scout = Scout()
    scout.start(tmp_path, grab=lambda: (screen, Region(0, 0, 900, 600)))
    wait_until(lambda: len(scout.boxes) == 2)
    boxes = {box["name"]: box for box in scout.boxes}
    assert boxes["Lobby.Play"]["found"] and (boxes["Lobby.Play"]["x"], boxes["Lobby.Play"]["y"]) == (300, 200)
    assert not boxes["Lobby.Gone"]["found"]
    assert scout.found == 1 and scout.isOn
    wait_until(lambda: scout.seen == 1)
    assert scout.notSeen == 1 and scout.total == 2
    scout.stop()
    assert not scout.isOn and scout.boxes == []
    assert scout.seen == 1  # the session's record stays while Scout is hidden
    scout.start(tmp_path, grab=lambda: (screen, Region(0, 0, 900, 600)), land_on="Lobby.Play")
    wait_until(lambda: len(scout.boxes) == 2)  # every image still, landed on the one picked in the Library
    assert scout.landed == "Lobby.Play"
    scout.stop()
    from darbit.core import targets

    wait_until(lambda: not targets._images and not targets._loaded)  # its images' pixels let go once it's off


def test_the_librarys_pictures_go_to_qml_as_files_with_the_same_bytes(tmp_path):
    import base64

    from darbit.studio.pictures import Pictures

    png = base64.b64encode(b"PNG made up").decode("ascii")
    pictures = Pictures(tmp_path)
    taken = pictures.take(
        [{"name": "A", "thumbnail": "data:image/png;base64," + png}, {"name": "B", "thumbnail": None}],
        "thumbnail",
        "thumbnail",
    )
    path = Path(QtCore.QUrl(taken[0]["thumbnail"]).toLocalFile())
    assert taken[0]["thumbnail"].startswith("file:") and path.read_bytes() == b"PNG made up"
    assert taken[1] == {"name": "B", "thumbnail": None}
    pictures.take([], "thumbnail", "thumbnail")  # gone from the Library: its file goes too
    assert not path.exists()


def test_scout_keeps_a_record_of_each_image_with_the_latest_shot_of_each_screen(qt, tmp_path, monkeypatch):
    import cv2
    import numpy as np

    from darbit.core.geometry import Region
    from darbit.studio import scout as scout_module
    from darbit.studio.scout import Scout

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "hi-bot"\n', encoding="utf-8")
    (tmp_path / "images").mkdir()
    for name in ("Shop.Buy", "Shop.Back", "Card.Rin", "Daily.Claim"):
        cv2.imwrite(str(tmp_path / "images" / f"{name}.png"), np.zeros((10, 10, 3), np.uint8))
    scout = Scout()
    scout.start(tmp_path, grab=lambda: (np.zeros((600, 900, 3), np.uint8), Region(0, 0, 900, 600)))
    scout.stop()
    pixels = np.full((600, 900, 3), 90, np.uint8)
    origin = Region(-100, 0, 900, 600)

    def box(name, score, x, found=True, alike=()):
        return {
            "name": name,
            "found": found,
            "score": score,
            "needs": 0.9,
            "x": x,
            "y": 50,
            "w": 40,
            "h": 20,
            "with": list(alike),
        }

    clock = [1000.0]
    monkeypatch.setattr(scout_module.time, "time", lambda: clock[0])
    scout.note(
        [
            box("Shop.Buy", 0.86, 0, found=False),
            box("Shop.Back", 0.99, 200),
            box("Card.Rin", 0.95, 400, alike=["Card.Aki"]),
        ],
        pixels,
        origin,
    )
    images = {image["name"]: image for image in scout.images}
    assert images["Shop.Back"]["state"] == "seen" and images["Shop.Back"]["seenOn"] == "Shop"
    assert images["Shop.Buy"]["state"] == "weak"  # found under what it needs
    assert images["Card.Rin"]["state"] == "weak" and images["Card.Rin"]["alike"] == ["Card.Aki"]
    assert images["Card.Rin"]["seenOn"] == "Shop"  # the screen showing, not the one in its name
    assert images["Daily.Claim"]["state"] == "not" and images["Daily.Claim"]["screen"] == "Daily"
    shot = scout_module.shots_folder(tmp_path) / "Shop.jpg"
    assert shot.is_file() and images["Shop.Back"]["shot"] == str(shot)
    assert images["Shop.Back"]["box"] == [300, 50, 40, 20]  # in the shot's own pixels
    assert (scout.seen, scout.weak, scout.notSeen, scout.total) == (1, 2, 1, 4)
    written = shot.stat().st_mtime_ns
    clock[0] += 1
    scout.note([box("Shop.Back", 0.995, 200)], pixels, origin)  # nothing new on the screen: the shot stays
    assert shot.stat().st_mtime_ns == written
    assert {image["name"]: image for image in scout.images}["Shop.Buy"]["shot"] == str(shot)
    scout.reset()
    assert scout.seen == 0 and scout.notSeen == 4 and scout.images[0]["shot"] == ""


def _scout_bot(tmp_path):
    """A bot with images on two screens, a Region and a Location, and a Scout that has seen some of them."""
    import json

    import cv2
    import numpy as np

    from darbit.core.geometry import Region
    from darbit.studio.scout import Scout

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "hi-bot"\n', encoding="utf-8")
    images = tmp_path / "images"
    images.mkdir()
    for name in ("Shop.Back", "Shop.Buy", "Shop.Card", "Daily.Claim"):
        cv2.imwrite(str(images / f"{name}.png"), np.full((20, 40, 3), 120, np.uint8))
    (images / "Shop.List.json").write_text(json.dumps({"kind": "region", "region": [10, 10, 300, 200]}))
    (images / "Shop.Spot.json").write_text(json.dumps({"kind": "location", "location": [50, 60]}))
    (images / "Shop.Buy.json").write_text(json.dumps({"kind": "image", "similarity": 0.9}))
    from darbit.platform.backend import NotSupported

    def grab():
        raise NotSupported("the test feeds the passes")

    scout = Scout()
    scout.start(tmp_path, grab=grab)

    def box(name, score, x):
        return {
            "name": name,
            "found": score >= 0.9,
            "score": score,
            "needs": 0.9,
            "x": x,
            "y": 40,
            "w": 40,
            "h": 20,
            "with": [],
            "shown": True,
            "region": None,
        }

    boxes = [box("Shop.Back", 0.99, 100), box("Shop.Buy", 0.86, 200), box("Shop.Card", 0.95, 300)]
    scout.note(boxes, np.full((300, 400, 3), 70, np.uint8), Region(0, 0, 400, 300))
    scout._take(boxes, 40.0)
    return scout


def test_scout_steps_through_a_group_and_lands_on_its_first(qt, tmp_path):
    from darbit.studio.scout import places_of

    scout = _scout_bot(tmp_path)
    assert (scout.seen, scout.weak, scout.notSeen) == (2, 1, 1)
    assert [image["name"] for image in scout.listed] == ["Shop.Buy", "Daily.Claim", "Shop.Back", "Shop.Card"]
    scout.setGroup("seen")
    assert [image["name"] for image in scout.listed] == ["Shop.Back", "Shop.Card"]
    assert scout.landed == "Shop.Back"  # landed on the group's first
    scout.next()
    assert scout.landed == "Shop.Card"
    scout.next()
    assert scout.landed == "Shop.Back"  # round again
    scout.previous()
    assert scout.landed == "Shop.Card"
    scout.setGroup("nothing")  # not a group: nothing changes
    assert scout.group == "seen"
    scout.setGroup("not")
    assert scout.landed == "Daily.Claim"
    assert scout.present == ["Shop"]
    assert places_of(tmp_path) == [
        {"name": "Shop.List", "kind": "region", "screen": "Shop", "box": [10, 10, 300, 200]},
        {"name": "Shop.Spot", "kind": "location", "screen": "Shop", "box": [50, 60, 0, 0]},
    ]  # an image's settings file isn't a place
    assert scout.places == places_of(tmp_path)
    buy = next(image for image in scout.images if image["name"] == "Shop.Buy")
    assert buy["shown"] == "image://scout/Shop/1" and buy["shotSize"] == [400, 300]
    assert not scout.shots.get("Shop").isNull()  # the shot, small, for the pill
    scout.forget("Shop.Buy")  # taken again
    assert next(image for image in scout.images if image["name"] == "Shop.Buy")["state"] == "not"
    scout.stop()


def test_scouts_lists_are_built_again_only_when_what_they_show_changes(qt, tmp_path):
    import numpy as np

    from darbit.core.geometry import Region

    scout = _scout_bot(tmp_path)
    told = []
    scout.recordChanged.connect(lambda: told.append(1))
    boxes = [dict(box) for box in scout.boxes]
    for _ in range(3):  # the same screen, pass after pass: the pill's lists stay as they are (hover, scrolling)
        scout.note(boxes, np.full((300, 400, 3), 70, np.uint8), Region(0, 0, 400, 300))
        scout._take(boxes, 41.0)
    assert told == []
    boxes[1] = {**boxes[1], "score": 0.93, "found": True}  # Shop.Buy found as it needs now
    scout.note(boxes, np.full((300, 400, 3), 70, np.uint8), Region(0, 0, 400, 300))
    scout._take(boxes, 41.0)
    assert told == [1] and scout.weak == 0
    scout.stop()


def _scout_pill(tmp_path, where):
    """Scout's pill dragged to `where` on a 1600 x 900 screen, with its engine."""
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.docking import PillPlace, Rect
    from darbit.studio.hiding import HidingPill

    scout = _scout_bot(tmp_path)
    place = PillPlace("scout", screens=lambda: {"main": Rect(0, 0, 1600, 900)}, keep=False)
    hiding = HidingPill(watch=lambda moved: None)
    studio = backend.Studio(FakeClient)
    engine = app.load(studio, scout=scout, scout_hiding=hiding, pill_places={"scout": place})
    root = engine.rootObjects()[0]
    pill = root.findChild(QQuickWindow, "scoutPill")
    wait_until(lambda: hiding.isOpen)
    place.begin(800, 30)
    place.move(*where)
    place.end()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    pill.setProperty("heldRoot", root)  # held, or Qt deletes the window under findChild
    return scout, studio, (engine, root), pill


def _named(window, name):
    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    return next((item for item in walk(window.contentItem()) if item.objectName() == name), None)


def test_scouts_pill_docked_on_top_steps_through_tiles_and_retakes_the_one_landed_on(qt, tmp_path):
    scout, studio, engine, pill = _scout_pill(tmp_path, (800, 3))
    assert pill.property("form") == "row"
    scout.setGroup("weak")
    strip = _named(pill, "scoutStrip")
    wait_until(strip.isVisible)
    tiles = _named(pill, "scoutTiles")
    wait_until(lambda: tiles.property("count") == 1)
    assert _named(pill, "scoutLandedLine").property("text").startswith("Image · seen on Shop now · best 0.86")
    on_shot, now = [], []
    studio.captureOnShotWanted.connect(lambda *args: on_shot.append(args))
    studio.captureWanted.connect(lambda *args: now.append(args))
    QMetaObject.invokeMethod(_named(pill, "stripRetakeOnShot"), "clicked")
    QMetaObject.invokeMethod(_named(pill, "stripRetakeNow"), "clicked")
    shot = str(tmp_path / ".darbit" / "scout" / "Shop.jpg")
    assert on_shot == [("/bots/ad-bot", "Shop.Buy", "image", shot)]
    assert now == [("/bots/ad-bot", "one", "Shop.Buy", "image")]
    scout.setGroup("not")  # one never seen: only the screen now
    wait_until(lambda: scout.landed == "Daily.Claim")
    wait_until(lambda: not _named(pill, "stripRetakeOnShot").isVisible())
    scout.stop()
    del engine


def test_scouts_pill_before_anything_is_seen_says_so(qt, tmp_path):
    scout, _studio, engine, pill = _scout_pill(tmp_path, (800, 3))
    scout.reset()
    scout.setGroup("seen")
    empty = _named(pill, "scoutEmpty")
    wait_until(empty.isVisible)
    assert empty.property("title") == "Nothing seen yet"
    assert empty.property("action") == ""
    scout.stop()
    del engine


def test_scouts_pill_on_a_side_lists_the_groups_and_floating_shows_a_grid_then_one_in_full(qt, tmp_path):
    scout, studio, engine, pill = _scout_pill(tmp_path, (1597, 450))
    assert pill.property("form") == "column"
    lines = _named(pill, "scoutLines")
    wait_until(lambda: lines.isVisible() and lines.property("count") == 4)
    assert not _named(pill, "scoutStrip").isVisible()  # the strip is the row's
    pill.setProperty("folded", {"seen": True})  # a group folded away keeps only its heading
    wait_until(lambda: lines.property("count") == 3)
    scout.stop()
    del engine

    (tmp_path / "again").mkdir()
    scout, studio, engine, pill = _scout_pill(tmp_path / "again", (1100, 450))
    assert pill.property("form") == "card"
    grid = _named(pill, "scoutGrid")
    wait_until(grid.isVisible)
    QMetaObject.invokeMethod(pill, "open", Q_ARG("QVariant", "Shop.Buy"))
    detail = _named(pill, "scoutDetail")
    wait_until(lambda: detail.isVisible() and not grid.isVisible())
    assert scout.group == "all" and scout.landed == "Shop.Buy"
    wanted = []
    studio.captureOnShotWanted.connect(lambda *args: wanted.append(args))
    QMetaObject.invokeMethod(_named(pill, "detailRetakeOnShot"), "clicked")
    assert wanted and wanted[0][1] == "Shop.Buy"
    QMetaObject.invokeMethod(_named(pill, "scoutBack"), "clicked")
    wait_until(grid.isVisible)
    scout.stop()
    del engine


def test_scout_shows_the_shared_pill_while_it_is_on(qt, tmp_path):
    import cv2
    import numpy as np
    from PySide6.QtCore import QObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.core.geometry import Region
    from darbit.studio.hiding import HidingPill
    from darbit.studio.scout import Scout

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "hi-bot"\n', encoding="utf-8")
    (tmp_path / "images").mkdir()
    screen = np.zeros((600, 900, 3), np.uint8)
    screen[200:260, 300:420] = (40, 160, 220)
    cv2.imwrite(str(tmp_path / "images" / "Menu.Start.png"), screen[190:270, 290:430])
    scout, hiding = Scout(), HidingPill(watch=lambda moved: None)
    engine = app.load(backend.Studio(FakeClient), scout=scout, scout_hiding=hiding)
    root = engine.rootObjects()[0]
    pill = root.findChild(QQuickWindow, "scoutPill")
    assert not hiding.isOpen and not pill.isVisible()
    scout.start(tmp_path, grab=lambda: (screen, Region(0, 0, 900, 600)))
    wait_until(lambda: scout.found == 1)
    assert hiding.isOpen and pill.isVisible()
    wait_until(lambda: pill.findChild(QObject, "scoutSeen").property("text") == "Scout: 1 of 1 seen")
    scout.stop()
    assert not hiding.isOpen and not pill.isVisible()
    del engine


def test_pictures_found_on_the_same_spot_are_look_alikes():
    from darbit.studio.scout import mark_look_alikes

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


@pytest.mark.parametrize("known", [True, False])
@pytest.mark.parametrize("shape", [(40, 160), (160, 100)])  # (height, width): a wide and a tall 160 px file
def test_a_thumbnail_is_decoded_at_the_size_it_is_drawn(qt, tmp_path, known, shape):
    import cv2
    import numpy as np
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    picture = tmp_path / "picture.png"
    cv2.imwrite(str(picture), np.full((*shape, 3), 128, np.uint8))
    size = f"pictureSize: [{shape[1]}, {shape[0]}];" if known else ""
    folder = (Path(app.__file__).parent / "qml").as_uri()
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    qml = f'import QtQuick\nimport "{folder}"\nThumbnail {{ width: 170; height: 100; {size} source: "{picture.as_uri()}" }}'
    component.setData(qml.encode(), QtCore.QUrl())
    thumbnail = component.create()
    assert thumbnail is not None, component.errors()
    # Qt's default with both sides given covers the box (a 160x40 picture became 400x100); this fits inside it
    wait_until(lambda: thumbnail.property("paintedWidth") > 0 and thumbnail.property("implicitWidth") <= 171)
    wait_until(lambda: thumbnail.property("implicitHeight") <= 101)
    drawn = (thumbnail.property("paintedWidth"), thumbnail.property("paintedHeight"))
    decoded = (thumbnail.property("implicitWidth"), thumbnail.property("implicitHeight"))
    assert max(abs(a - b) for a, b in zip(drawn, decoded)) <= 1


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


class Window(QtCore.QObject):
    """The Studio's window: shown or not, closed to the tray or minimized."""

    closing = QtCore.Signal()
    visibilityChanged = QtCore.Signal(object)
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


def test_the_run_pill_moves_to_a_side_as_a_column_floats_as_a_card_and_docks_again(qt):
    from PySide6.QtCore import QObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.docking import GAP, PillPlace
    from darbit.studio.hiding import HidingPill

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        hiding = HidingPill(watch=lambda on_move: lambda: None)
        place = PillPlace("run")
        studio = backend.Studio(FakeClient)
        engine = app.load(studio, run_pill=hiding, pill_places={"run": place})
        root = engine.rootObjects()[0]  # held, or Qt deletes it
        studio.connect()
        wait_until(lambda: studio.bot.get("name") == "ad-bot")
        hiding.open()
        window = root.findChild(QQuickWindow, "runPill")
        wait_until(window.isVisible)
        screen = window.screen().geometry()
        wait_until(lambda: window.y() < 40)  # docked at the top centre, a row
        assert abs(window.x() + window.width() / 2 - screen.center().x()) < 4 and window.width() > window.height()
        place.begin(screen.center().x(), 30)
        place.move(screen.left() + 20, screen.center().y())
        assert window.property("form") == "column"  # it takes its edge's shape while it's dragged
        place.end()
        wait_until(lambda: window.height() > window.width())  # a column on the left edge
        # the pill itself sits by the edge; its window's clear margin (room for the tilt) may run past it
        wait_until(lambda: abs(window.x() + window.property("margin") - screen.left() - GAP) < 2)
        assert place.edge == "left"
        place.begin(screen.left() + 20, screen.center().y())
        place.move(screen.center().x(), screen.center().y())
        place.end()
        card = window.findChild(QObject, "pillCard")
        wait_until(lambda: card.property("visible"))
        assert place.floating and not hiding.tucked
        place.dock()  # the card's Dock
        wait_until(lambda: not card.property("visible"))
        assert place.edge == "left"
        hiding.close()
        del engine
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


def test_a_dragged_pills_guide_shows_its_ghost_where_it_lands_and_a_glow_by_the_mouse(qt):
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.docking import GAP, PillPlace
    from darbit.studio.hiding import HidingPill

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        hiding = HidingPill(watch=lambda on_move: lambda: None)
        place = PillPlace("run", keep=False)
        studio = backend.Studio(FakeClient)
        engine = app.load(studio, run_pill=hiding, pill_places={"run": place})
        root = engine.rootObjects()[0]  # held, or Qt deletes it
        studio.connect()
        wait_until(lambda: studio.bot.get("name") == "ad-bot")
        hiding.open()
        window = root.findChild(QQuickWindow, "runPill")
        wait_until(window.isVisible)
        work = place.work
        bottom = work["y"] + work["height"]
        place.begin(work["x"] + work["width"] / 2, work["y"] + 30)
        place.move(work["x"] + 400, bottom - 60)  # toward the bottom edge: a row there
        windows = QtCore.QCoreApplication.instance().topLevelWindows()
        guide = next(item for item in windows if item.title() == window.title() + " guide")
        wait_until(guide.isVisible)
        ghost = _named(guide, "pillGhost")
        size = place.sizeOf("row")
        wait_until(lambda: ghost.opacity() == 1)
        assert (ghost.width(), ghost.height()) == pytest.approx((size["width"], size["height"]))  # the pill, as a row
        assert ghost.y() + ghost.height() == pytest.approx(bottom - GAP - guide.y())  # on the bottom edge
        before = ghost.x()
        place.move(work["x"] + 700, bottom - 60)
        wait_until(lambda: ghost.x() > before)  # it follows the mouse along the edge
        assert place.pointer == {"x": work["x"] + 700, "y": bottom - 60}  # the glow's place
        place.move(work["x"] + work["width"] / 2, work["y"] + work["height"] / 2)  # into the middle: it would float
        wait_until(lambda: ghost.opacity() == 0)
        place.cancel()
        wait_until(lambda: not guide.isVisible())
        hiding.close()
        del engine
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


@pytest.mark.parametrize("moving", [False, True])
def test_a_dragged_pill_keeps_its_window_while_it_changes_form_and_lands_above_the_taskbar(qt, tmp_path, moving):
    from PySide6.QtCore import QObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.docking import GAP, PillPlace, Rect
    from darbit.studio.hiding import HidingPill

    _keep_effects(tmp_path, moving)  # with effects on it lands on the clock; off, at once
    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        box = QtCore.QRect(0, 0, 2400, 1200)  # room for the row to move along its edge
        work = Rect(box.x(), box.y(), box.width(), box.height() - 48)  # a taskbar along the bottom
        screens = {"main": Rect(box.x(), box.y(), box.width(), box.height(), work=work)}
        hiding = HidingPill(watch=lambda on_move: lambda: None)
        place = PillPlace("run", screens=lambda: screens, keep=False)
        studio = backend.Studio(FakeClient)
        engine = app.load(studio, run_pill=hiding, pill_places={"run": place})
        root = engine.rootObjects()[0]  # held, or Qt deletes it
        studio.connect()
        wait_until(lambda: studio.bot.get("name") == "ad-bot")
        hiding.open()
        window = root.findChild(QQuickWindow, "runPill")
        wait_until(window.isVisible)
        face = window.findChild(QObject, "pillFace")
        row = _steady_width(face)  # laid out with the bot's line, done easing to its width
        place.begin(box.center().x(), 30)
        wait_until(lambda: window.property("roomy"))
        held = (window.width(), window.height())
        assert held[0] > 2 * face.property("width") and held[1] > 2 * face.property("height")  # room for any form
        place.move(box.left() + 20, box.center().y())
        assert window.property("form") == "column"
        assert (window.width(), window.height()) == held  # a new form redraws inside it: the window only moves
        place.move(box.center().x() + 100, box.bottom() - 60)
        # held there a moment, as a hand does: the row lays itself out at its own size
        wait_until(lambda: place.sizeOf("row")["width"] == face.property("width") == row)
        place.end()
        wait_until(lambda: not window.property("roomy"))
        wait_until(lambda: window.height() < window.width())  # a row again, its own size
        margin = window.property("margin")
        bottom = window.y() + margin + face.property("height")
        assert abs(bottom - (work.bottom - GAP)) < 2  # above the taskbar, not under it
        middle = window.x() + margin + face.property("width") / 2
        assert abs(middle - (box.center().x() + 100)) < 2  # where it was let go, with no slide after it lands
        hiding.close()
        del root, engine
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


def _steady_width(item, checks=8):
    """An item's width once it has stopped changing (an animation runs on its frames, 16 ms apart)."""
    seen = []

    def steady():
        seen.append(item.property("width"))
        return len(seen) >= checks and len(set(seen[-checks:])) == 1

    wait_until(steady)
    return seen[-1]


def test_dragging_the_recorders_pill_keeps_the_drag_out_of_the_recording(qt):
    from darbit.studio.docking import PillPlace
    from darbit.studio.hiding import HidingPill
    from darbit.studio.recorder import Recorder

    recorder, hiding, place = Recorder(), HidingPill(watch=lambda on_move: lambda: None), PillPlace("recorder")
    engine = app.load(
        backend.Studio(FakeClient), recorder=recorder, recorder_hiding=hiding, pill_places={"recorder": place}
    )
    root = engine.rootObjects()[0]  # held, or Qt deletes it
    hiding.open()
    screen = QGuiApplication.primaryScreen().geometry()
    wait_until(lambda: 0 < recorder._area[3] < screen.height() / 4)  # docked: only the pill is left out
    place.begin(screen.center().x(), 30)
    wait_until(lambda: recorder._area == [screen.x(), screen.y(), screen.width(), screen.height()])
    place.move(screen.center().x(), screen.bottom() - 10)  # the release lands anywhere on the screen: left out too
    assert recorder._area[2] == screen.width()
    place.end()
    wait_until(lambda: 0 < recorder._area[3] < screen.height() / 4 and recorder._area[1] > screen.height() / 2)
    hiding.close()
    del root, engine


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


def test_scout_lands_on_one_image_from_the_library(qt):
    client = FakeClient()
    studio = backend.Studio(lambda: client)
    wanted = []
    studio.scoutWanted.connect(lambda folder, name: wanted.append((folder, name)))
    studio.connect()
    wait_until(lambda: studio.bot.get("path"))
    studio.scoutOne("Bag.Equip")
    studio.toggleScout()  # its key: every image, on or off
    assert wanted == [("/bots/ad-bot", "Bag.Equip"), ("/bots/ad-bot", "")]


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
    found = studio_capture.saved_shot(path)
    assert found.pixels.shape == (300, 400, 3) and found.pixels.min() == 255
    assert found.origin == Region(0, 0, 400, 300) and not found.lossy
    monkeypatch.setattr(studio_capture.screen, "desktop", lambda: Region(0, 0, 400, 400))
    assert studio_capture.saved_shot(path) is None  # the screens are laid out differently now
    monkeypatch.setattr(studio_capture.screen, "desktop", lambda: Region(-400, 0, 800, 300))
    assert studio_capture.saved_shot(tmp_path / "gone.jpg") is None
    pixels = found.pixels
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
    studio.retakeOn("Rod.Cast", "image", "C:/bots/ad-bot/screens/Rod.jpg")  # a path, from the Library or Scout
    assert wanted == [
        ("/bots/ad-bot", "Rod.Cast", "image", str(path).replace("\\", "/")),
        ("/bots/ad-bot", "Rod.Cast", "image", "C:/bots/ad-bot/screens/Rod.jpg"),
    ]


def test_a_saved_shot_of_the_main_screen_is_used_as_it_is_and_a_lossless_twin_before_its_jpeg(
    qt, tmp_path, monkeypatch
):
    import cv2
    import numpy as np

    from darbit.core.geometry import Region
    from darbit.studio import capture as studio_capture

    monkeypatch.setattr(studio_capture.screen, "desktop", lambda: Region(-400, 0, 800, 300))
    monkeypatch.setattr(studio_capture.screen, "monitors", lambda: [Region(0, 0, 400, 300), Region(-400, 0, 400, 300)])
    jpeg = tmp_path / "Menu.jpg"
    cv2.imwrite(str(jpeg), np.full((300, 400, 3), 90, np.uint8))  # a screen's last shot: the main screen only
    found = studio_capture.saved_shot(jpeg)
    assert found.pixels.shape == (300, 400, 3) and found.lossy  # at its own pixels, and said to be softer
    assert found.origin == Region(0, 0, 400, 300)
    cv2.imwrite(str(tmp_path / "Menu.png"), np.full((300, 400, 3), 200, np.uint8))
    found = studio_capture.saved_shot(jpeg)
    assert not found.lossy and found.pixels.min() == 200  # the lossless one is used where there is one
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "fish-bot"\n', encoding="utf-8")
    capture = studio_capture.Capture(studio_capture.ShotProvider())
    capture.start(tmp_path, "one", "Rod.Cast", "image", shot=found.pixels, origin=found.origin, lossy=True)
    assert "JPEG" in capture.property("shotNote")
    capture.close()
    assert capture.property("shotNote") == ""


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


def test_closing_or_minimizing_the_studio_with_a_bot_running_opens_the_run_pill(qt):
    from PySide6.QtGui import QWindow

    from darbit.studio.hiding import HidingPill

    client = Runs()
    studio = backend.Studio(lambda: client)
    pill = HidingPill(watch=lambda on_move: lambda: None)
    window = Window()
    app._connect_run_pill(studio, pill, window)
    studio.connect()
    wait_until(lambda: studio.bot.get("status") == "stopped")
    window.closing.emit()
    assert not pill.isOpen  # control: no bot runs, nothing to keep in reach
    client.status = "running"
    studio._on_event("project.status", {"path": BOT["path"], "status": "running"})
    wait_until(lambda: pill.isOpen)
    pill.close()  # ⤢: the Studio is back, the bot still running
    assert window.shown and not pill.isOpen
    window.closing.emit()
    assert pill.isOpen
    window.visibilityChanged.emit(QWindow.Windowed)  # the Studio opened again
    assert not pill.isOpen
    window.visibilityChanged.emit(QWindow.Minimized)
    assert pill.isOpen
    pill.close()
    studio.setRunPill(False)  # off: closing leaves no pill
    window.closing.emit()
    assert not pill.isOpen


def test_closing_the_studio_shows_another_running_bot_in_the_run_pill(qt):
    from darbit.studio.hiding import HidingPill

    client = FakeClient()  # ad-bot runs; "other" doesn't
    studio = backend.Studio(lambda: client, bot="/bots/other")
    pill = HidingPill(watch=lambda on_move: lambda: None)
    window = Window()
    app._connect_run_pill(studio, pill, window)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "other")
    window.closing.emit()
    assert pill.isOpen and studio.bot.get("name") == "ad-bot"


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
    sheets = {"Sheet"}  # every sheet over the Studio is a Sheet: one frame
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
    # the side panel retakes it on the shot it was taken on, or on the screen now
    on_shot = next(item for item in walk(window.contentItem()) if item.objectName() == "retakeOnSavedShot")
    wait_until(on_shot.isVisible)
    wanted = []
    studio.captureOnShotWanted.connect(lambda *args: wanted.append(args))
    QMetaObject.invokeMethod(on_shot, "clicked")
    assert wanted == [("/bots/ad-bot", "Bag.Equip", "image", "C:/bots/ad-bot/screens/Bag.jpg")]
    page.setProperty("showScreens", False)  # the grid has no saved shot to offer
    wait_until(lambda: not on_shot.isVisible())
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

    # it opens on today, with no run yet: the link goes to the last day that has runs
    wait_until(lambda: find("todayEmpty") is not None and find("todayEmpty").isVisible())
    QMetaObject.invokeMethod(find("todayEmpty"), "acted")
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
    wait_until(lambda: _named(window, "todayEmpty") is not None and _named(window, "todayEmpty").isVisible())
    QMetaObject.invokeMethod(_named(window, "todayEmpty"), "acted")  # no run today: the last day with runs
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


class Checking(FakeClient):
    """The service, with darbit doctor's checks finding `problems` (None: a service that can't check)."""

    def __init__(self, problems=0):
        super().__init__()
        self.problems = problems

    def call(self, method, **params):
        if method != "bot.doctor":
            return super().call(method, **params)
        self.asked.append((method, params))
        if self.problems is None:
            from darbit.service.client import ServiceError

            raise ServiceError("no method bot.doctor")
        checks = [{"name": "darbit.toml", "ok": True, "found": "ad-bot 1.0.0", "fix": "", "missing": []}]
        if self.problems:
            checks.append(
                {
                    "name": "targets",
                    "ok": False,
                    "found": "2 of 14 not taken: Bag.Equip, Lobby.Play",
                    "fix": "take them with Capture in darbit Studio (darbit app)",
                    "missing": ["Bag.Equip", "Lobby.Play"],
                }
            )
        return {"checks": checks, "problems": self.problems}


@pytest.mark.parametrize("problems", [0, None])
def test_play_starts_at_once_when_the_checks_find_nothing(qt, problems):
    client = Checking(problems)
    studio = backend.Studio(lambda: client)
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    found = []
    studio.checksFound.connect(lambda: found.append(True))
    studio.play()
    wait_until(lambda: ("bot.start", {"bot": "/bots/ad-bot"}) in client.asked)
    assert ("bot.doctor", {"bot": "/bots/ad-bot"}) in client.asked
    assert found == []


def test_play_shows_the_checks_when_they_find_a_problem_with_start_anyway(qt):
    from PySide6.QtCore import QObject

    client = Checking(1)
    studio = backend.Studio(lambda: client)
    engine = app.load(studio)
    root = engine.rootObjects()[0]
    wait_until(lambda: studio.bot.get("name") == "ad-bot")
    studio.play()
    sheet = root.findChild(QObject, "checksSheet")
    wait_until(lambda: sheet.property("opened"))
    assert not any(method == "bot.start" for method, _ in client.asked)

    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    def button(name):
        return next(item for item in walk(sheet.property("contentItem")) if item.objectName() == name)

    wanted = []
    studio.captureWanted.connect(lambda *args: wanted.append(args))
    QMetaObject.invokeMethod(button("takeThem"), "clicked")
    assert wanted == [("/bots/ad-bot", "guide", "", "image")]  # the guide's targets not taken
    sheet.setProperty("visible", True)
    wait_until(lambda: sheet.property("opened"))
    QMetaObject.invokeMethod(button("startAnyway"), "clicked")
    wait_until(lambda: ("bot.start", {"bot": "/bots/ad-bot"}) in client.asked)
    wait_until(lambda: not sheet.property("visible"))
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


def test_capture_takes_several_targets_on_one_shot_and_a_retake_takes_one(qt, tmp_path):
    import json

    import numpy as np
    from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, Qt
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest

    from darbit.studio.capture import Capture, ShotProvider

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    screen = np.full((600, 800, 3), 30, np.uint8)
    noise = np.random.default_rng(7)
    for left in (100, 300, 500):  # three cards, each its own
        screen[200:300, left : left + 120] = noise.integers(0, 255, (100, 120, 3), dtype=np.uint8)
    capture = Capture(ShotProvider())
    engine = app.load(backend.Studio(FakeClient), capture)
    root = engine.rootObjects()[0]
    window = root.findChild(QQuickWindow, "captureWindow")
    name = window.findChild(QObject, "nameField")

    def value(key):
        found = window.property(key)
        return found.toVariant() if hasattr(found, "toVariant") else found

    def drag(start, end):
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPoint(*start))
        QTest.mouseMove(window, QPoint((start[0] + end[0]) // 2, (start[1] + end[1]) // 2))
        QTest.mouseMove(window, QPoint(*end))
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPoint(*end))
        QtCore.QCoreApplication.processEvents()

    capture.start(tmp_path, shot=screen)
    assert capture.several
    wait_until(window.isVisible)
    window.resize(800, 600)
    QtCore.QCoreApplication.processEvents()
    drag((100, 200), (220, 300))
    first = name.property("text")
    assert first.isdigit() and len(first) == 13  # a name to start with: the time, SikuliX's way
    drag((420, 300), (300, 200))  # away from the first: another target, the first one kept (clear of its readout)
    drag((620, 300), (500, 200))
    shown = value("shown")
    assert [entry["image"] for entry in shown] == [[100, 200, 120, 100], [300, 200, 120, 100], [500, 200, 120, 100]]
    assert len({entry["name"] for entry in shown}) == 3
    assert value("image") == [500, 200, 120, 100]  # the last one taken is the active one
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(150, 250))  # a click on a box makes it active
    assert value("image") == [100, 200, 120, 100] and name.property("text") == first
    QTest.keyClick(window, Qt.Key_Right)  # the arrows act on the active box
    assert value("image") == [101, 200, 120, 100]
    QTest.keyClick(window, Qt.Key_N)  # N: the next one
    assert value("image") == [300, 200, 120, 100]
    QTest.keyClick(window, Qt.Key_N, Qt.ShiftModifier)  # Shift+N: back
    assert value("image") == [101, 200, 120, 100]
    name.setProperty("text", "Shop.Aki")
    QTest.keyClick(window, Qt.Key_N)
    assert value("shown")[0]["name"] == "Shop.Aki"  # the name stays with its box
    QMetaObject.invokeMethod(window, "removeTarget", Q_ARG("QVariant", 2))
    assert len(value("shown")) == 2
    QMetaObject.invokeMethod(window, "undo")  # undo works per change: the removed one comes back
    assert len(value("shown")) == 3
    QMetaObject.invokeMethod(window, "test")  # Test checks every box on the shot
    wait_until(lambda: window.property("note").startswith("Test: 3 found once"))
    QMetaObject.invokeMethod(window, "save")  # Save saves them all
    images = sorted(path.stem for path in (tmp_path / "images").glob("*.json"))
    assert len(images) == 3 and "Shop.Aki" in images
    assert json.loads((tmp_path / "images" / "Shop.Aki.json").read_text(encoding="utf-8"))["kind"] == "image"
    wait_until(lambda: not capture.isOpen)  # nothing left: it closes
    # the control: a retake takes one; a box away from it replaces it, and no name is made up
    capture.start(tmp_path, "one", "Shop.Aki", "image", shot=screen)
    assert not capture.several
    wait_until(window.isVisible)
    drag((100, 200), (220, 300))
    drag((420, 300), (300, 200))
    assert len(value("shown")) == 1 and value("image") == [300, 200, 120, 100]
    assert name.property("text") == "Shop.Aki"
    capture.close()
    del engine


def test_capture_lists_the_targets_on_the_shot_as_tiles_in_its_pill(qt, tmp_path, monkeypatch):
    import numpy as np
    from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QSize, Qt
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest

    from darbit import paths
    from darbit.studio.capture import Capture, ShotProvider
    from darbit.studio.docking import PillPlace

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    monkeypatch.setattr(paths, "config_dir", lambda: tmp_path)
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "cap-bot"\n', encoding="utf-8")
    place = PillPlace("capture", keep=False, in_window=True)
    capture = Capture(ShotProvider())
    engine = app.load(backend.Studio(FakeClient), capture, pill_places={"capture": place})
    root = engine.rootObjects()[0]
    window = root.findChild(QQuickWindow, "captureWindow")
    capture.start(tmp_path, shot=np.zeros((600, 800, 3), np.uint8))
    wait_until(window.isVisible)
    row = window.findChild(QObject, "tilesRow")
    column = window.findChild(QObject, "tilesColumn")

    def call(name, *values):
        QMetaObject.invokeMethod(window, name, *[Q_ARG("QVariant", value) for value in values])

    def value(key):
        found = window.property(key)
        return found.toVariant() if hasattr(found, "toVariant") else found

    assert not row.property("visible")  # nothing taken yet: no tiles
    for index, left in enumerate((100, 300, 500)):
        if index:
            call("newTarget")
        call("setPart", "image", [left, 200, 120, 100])
    QtCore.QCoreApplication.processEvents()
    assert row.property("visible") and row.property("count") == 3  # top edge: one row of tiles, under the pill's row
    assert not column.property("visible")
    QMetaObject.invokeMethod(row, "picked", Q_ARG(int, 0))  # a tile makes its target the active one
    assert value("image") == [100, 200, 120, 100] and value("active") == 0
    QMetaObject.invokeMethod(row, "removed", Q_ARG(int, 1))  # ✕ drops it
    QtCore.QCoreApplication.processEvents()
    assert row.property("count") == 2
    call("undo")
    QtCore.QCoreApplication.processEvents()
    assert row.property("count") == 3
    window.setProperty("listOpen", False)  # the stack folds them away
    QtCore.QCoreApplication.processEvents()
    assert not row.property("visible")
    window.setProperty("listOpen", True)
    place.useArea(0, 0, window.width(), window.height())
    place.begin(400, 10)
    place.move(2, 300)  # to the left edge: a column, two tiles a row
    place.end()
    QtCore.QCoreApplication.processEvents()
    assert column.property("visible") and not row.property("visible") and column.property("count") == 3
    for left in range(10, 600, 100):  # more than fit: the tiles scroll
        call("newTarget")
        call("setPart", "image", [left, 400, 60, 50])
    QtCore.QCoreApplication.processEvents()
    call("activate", 0)
    QtCore.QCoreApplication.processEvents()
    end = column.property("contentHeight") - column.property("height")
    assert end > 0
    column.setProperty("contentY", end)
    QTest.keyClick(window, Qt.Key_Right)  # a nudge updates its tile in place: the list stays where it was scrolled
    QtCore.QCoreApplication.processEvents()
    assert column.property("contentY") == end
    QMetaObject.invokeMethod(window, "activate", Q_ARG("QVariant", 1))
    wait_until(lambda: column.property("contentY") < end)  # the active one's tile comes into sight
    # a tile's image is the shot's part under its box
    tile = capture.provider.requestImage("shot1/100,200,120,100", QSize(), QSize())
    assert (tile.width(), tile.height()) == (120, 100)
    assert capture.provider.requestImage("shot1", QSize(), QSize()).width() == 800  # the control: the whole shot
    capture.close()
    del engine
    QtCore.qInstallMessageHandler(None)
    assert warnings == []  # nothing in Capture's window or its tiles warns


def test_capture_resizes_the_box_by_dragging_its_edges_and_corners(qt, tmp_path):
    import numpy as np
    from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, Qt
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

    def box(name="image"):
        value = window.property(name)
        value = value.toVariant() if hasattr(value, "toVariant") else value
        return [round(number) for number in value]

    def drag(start, end):
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, QPoint(*start))
        QTest.mouseMove(window, QPoint((start[0] + end[0]) // 2, (start[1] + end[1]) // 2))
        QTest.mouseMove(window, QPoint(*end))
        QtCore.QCoreApplication.processEvents()
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, QPoint(*end))
        QtCore.QCoreApplication.processEvents()

    QMetaObject.invokeMethod(window, "setPart", Q_ARG("QVariant", "image"), Q_ARG("QVariant", [200, 200, 100, 80]))
    QtCore.QCoreApplication.processEvents()
    drag((250, 240), (260, 250))  # a drag from inside moves it, as before
    assert box() == [210, 210, 100, 80]
    drag((310, 225), (360, 225))  # its right edge, away from the handle: wider, the rest stays
    assert box() == [210, 210, 150, 80]
    at = magnifier.property("at")
    assert (round(at.x()), round(at.y())) == (360, 225)  # the magnifier followed the drag
    drag((211, 211), (190, 180))  # its top-left corner
    assert box() == [190, 180, 170, 110]
    drag((220, 290), (220, 400))  # its bottom edge
    assert box() == [190, 180, 170, 220]
    QMetaObject.invokeMethod(window, "undo")  # each drag is one undo step
    assert box() == [190, 180, 170, 110]
    QMetaObject.invokeMethod(window, "undo")
    assert box() == [210, 210, 150, 80]
    # a region resizes the same way when it's the kind picked (its edge grabbed below the pill and its tiles, which
    # sit over the top of the shot)
    QMetaObject.invokeMethod(window, "setPart", Q_ARG("QVariant", "region"), Q_ARG("QVariant", [100, 100, 400, 400]))
    QtCore.QCoreApplication.processEvents()
    drag((99, 400), (50, 400))  # its left edge
    assert box("region") == [50, 100, 450, 400]
    assert box() == [210, 210, 150, 80]  # the image stays
    capture.close()
    del engine


def test_capture_arrows_move_one_pixel_a_tap_and_speed_up_while_held(qt, tmp_path):
    import numpy as np
    from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, Qt
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
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(700, 500))  # the keys go to the shot, not the name
    QMetaObject.invokeMethod(window, "setPart", Q_ARG("QVariant", "image"), Q_ARG("QVariant", [100, 100, 50, 40]))

    def box():
        value = window.property("image")
        value = value.toVariant() if hasattr(value, "toVariant") else value
        return [round(number) for number in value]

    def hold(key, seconds, modifier=Qt.NoModifier):
        QTest.keyPress(window, key, modifier)
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.005)
        QTest.keyRelease(window, key, modifier)
        QtCore.QCoreApplication.processEvents()

    QTest.keyClick(window, Qt.Key_Right)
    assert box() == [101, 100, 50, 40]  # a tap: exactly 1 px
    hold(Qt.Key_Right, 0.3)
    assert box() == [102, 100, 50, 40]  # under half a second it's still a tap
    QTest.keyClick(window, Qt.Key_Down, Qt.ControlModifier)
    assert box() == [102, 100, 50, 41]  # Ctrl: its size, 1 px
    QTest.keyClick(window, Qt.Key_Left, Qt.ShiftModifier)
    assert box() == [92, 100, 50, 41]  # Shift: 10 px
    hold(Qt.Key_Right, 1.3)
    moved = box()[0] - 92
    assert moved > 60  # held: faster and faster
    QtCore.QCoreApplication.processEvents()
    time.sleep(0.1)
    QtCore.QCoreApplication.processEvents()
    assert box()[0] - 92 == moved  # and it stops when let go
    hold(Qt.Key_Right, 1.3, Qt.ControlModifier)
    assert box()[2] > 110  # Ctrl held: it grows the same way
    capture.close()
    del engine


def test_the_quit_item_says_what_happens_to_the_running_bots():
    assert backend.quit_label([], keep=False) == "Quit darbit Studio"  # control: no bot runs, nothing to say
    assert backend.quit_label(["ad-bot"], keep=False) == "Quit and stop ad-bot"
    assert backend.quit_label(["ad-bot", "watcher"], keep=False) == "Quit and stop 2 bots"
    assert backend.quit_label(["ad-bot"], keep=True) == "Quit (bots go on)"


def test_quitting_stops_every_running_bot_unless_darbit_settings_keep_them(qt):
    from darbit.server import ui_settings
    from darbit.studio.backend import KEEP_BOTS

    class Hides:
        shown = True

        def hide(self):
            self.shown = False

    client = FakeClient()  # ad-bot runs, "other" is stopped
    studio = backend.Studio(lambda: client)
    studio.connect()
    wait_until(lambda: studio.bots)
    assert not studio.keepBots and studio.running_names() == ["ad-bot"]
    window, tray = Hides(), Hides()
    app._stop_bots_on_quit(studio, window, tray)
    stopped = [params["bot"] for method, params in client.asked if method == "bot.stop"]
    assert stopped == ["/bots/ad-bot"]  # the stopped one isn't asked
    assert not window.shown and not tray.shown

    client.asked.clear()
    studio.setKeepBots(True)
    assert ui_settings.get(KEEP_BOTS) is True
    app._stop_bots_on_quit(studio, Hides(), Hides())
    assert not [method for method, params in client.asked if method == "bot.stop"]  # kept going
    assert backend.Studio(FakeClient).keepBots  # kept for next time
    studio.setKeepBots(False)  # the setting is shared by the tests that come after


def test_quitting_with_the_service_gone_stops_nothing_and_doesnt_raise(qt):
    from darbit.service.client import NotRunning

    class Gone(FakeClient):
        def call(self, method, **params):
            if method == "bots.list" and self.asked:
                raise NotRunning("the service went away")
            return super().call(method, **params)

    studio = backend.Studio(Gone)
    studio.connect()
    wait_until(lambda: studio.bots)
    studio.stop_every_bot()


def test_the_tray_panel_opens_by_the_icon_on_every_taskbar_edge():
    from PySide6.QtCore import QPoint, QRect, QSize

    from darbit.studio.tray import GAP, panel_place, taskbar_edge

    screen = QRect(0, 0, 1920, 1080)
    size = QSize(336, 400)
    bottom = QRect(0, 0, 1920, 1032)
    assert taskbar_edge(QRect(1700, 1040, 24, 24), screen, bottom) == "bottom"
    assert panel_place(QRect(1700, 1040, 24, 24), screen, bottom, size) == QPoint(1712 - 168, 1032 - GAP - 400)
    top = QRect(0, 48, 1920, 1032)
    assert panel_place(QRect(1700, 12, 24, 24), screen, top, size) == QPoint(1712 - 168, 48 + GAP)
    left = QRect(60, 0, 1860, 1080)
    assert panel_place(QRect(18, 900, 24, 24), screen, left, size) == QPoint(60 + GAP, 1080 - GAP - 400)  # kept on
    right = QRect(0, 0, 1860, 1080)
    assert panel_place(QRect(1878, 500, 24, 24), screen, right, size) == QPoint(1860 - GAP - 336, 312)
    # a taskbar that hides itself leaves the whole screen free: the edge nearest the icon
    assert taskbar_edge(QRect(1700, 1056, 24, 24), screen, screen) == "bottom"
    assert taskbar_edge(QRect(4, 500, 24, 24), screen, screen) == "left"
    # control: an icon in a corner still gets the whole panel on the screen
    corner = panel_place(QRect(1900, 1040, 24, 24), screen, bottom, size)
    assert corner.x() + 336 <= 1920 - GAP and corner.x() == 1920 - GAP - 336


def test_the_tray_panel_opens_above_the_taskbar_in_the_pills_work_area():
    from PySide6.QtCore import QRect, QSize

    from darbit.platform.system import HiddenTaskbar
    from darbit.studio.docking import Rect, less_taskbars, work_of
    from darbit.studio.tray import GAP, as_qrect, icon_in_points, panel_place, screen_with

    # 2560 x 1600 pixels at 150%: 1707 x 1067 points, a 72-pixel taskbar along the bottom (work area 1019 high)
    laptop = Rect(0, 0, 1707, 1067, 1.5, work=Rect(0, 0, 1707, 1019))
    side = Rect(2560, 0, 1920, 1080)  # a 100% screen on its right, starting where the laptop's pixels end
    screens = [laptop, side]
    size = QSize(336, 324)
    # Windows tells the icon's place in its pixels; in points it is on the taskbar, under the work area
    icon = icon_in_points(QRect(2183, 1528, 48, 72), screens)
    assert icon == QRect(1455, 1019, 32, 48)
    assert screen_with(icon, screens) is laptop
    spot = panel_place(icon, as_qrect(laptop), as_qrect(work_of(laptop)), size)
    assert spot.y() + size.height() == 1019 - GAP  # its bottom above the taskbar, by the icon
    assert abs(spot.x() + 168 - (1455 + 16)) <= 1
    # a taskbar that hides itself still gets its room: Windows counts the whole screen free
    hiding = Rect(0, 0, 1707, 1067, 1.5)
    hiding.work = less_taskbars(hiding, Rect(0, 0, 1707, 1067), [HiddenTaskbar("bottom", 72)])
    spot = panel_place(QRect(1455, 1040, 32, 24), as_qrect(hiding), as_qrect(work_of(hiding)), size)
    assert spot.y() + size.height() == 1019 - GAP
    # control: an icon already in points, on the second screen, is left as it is
    assert icon_in_points(QRect(3000, 1040, 24, 24), screens) == QRect(3000, 1040, 24, 24)
    assert screen_with(QRect(3000, 1040, 24, 24), screens) is side


def test_the_tray_panel_opens_outside_the_hidden_icons_flyout_above_a_bottom_taskbar():
    from PySide6.QtCore import QRect, QSize

    from darbit.studio.docking import Rect, work_of
    from darbit.studio.tray import GAP, as_qrect, flyout_taken, icon_in_points, panel_place

    # 2560 x 1600 pixels at 150%, a 72-pixel taskbar along the bottom; the flyout as Windows 11 tells it, in pixels
    laptop = Rect(0, 0, 1707, 1067, 1.5, work=Rect(0, 0, 1707, 1019))
    screens = [laptop, Rect(2560, 0, 1920, 1080)]
    flyout = QRect(2032, 1357, 351, 171)
    icon = QRect(2183, 1400, 48, 48)  # in the flyout
    taken = flyout_taken(icon, flyout, screens)
    assert taken == QRect(1355, 905, 234, 114)
    work = as_qrect(work_of(laptop))
    size = QSize(336, 324)
    spot = panel_place(icon_in_points(icon, screens), as_qrect(laptop), work, size, taken)
    panel = QRect(spot, size)
    assert panel.bottom() + 1 == 905 - GAP  # above the flyout, lined up with the icon
    assert work.contains(panel) and not panel.intersects(taken)
    # no room above a tall flyout: beside it, on the side with more room, still above the taskbar
    tall = QRect(1355, 200, 234, 819)
    spot = panel_place(icon_in_points(icon, screens), as_qrect(laptop), work, size, tall)
    panel = QRect(spot, size)
    assert panel.right() + 1 == 1355 - GAP and panel.bottom() + 1 == 1019 - GAP
    assert work.contains(panel) and not panel.intersects(tall)
    # control: an icon on the taskbar itself, with the flyout open, opens where it always did
    pinned = QRect(1900, 1540, 48, 48)
    assert flyout_taken(pinned, flyout, screens) is None
    by_icon = icon_in_points(pinned, screens)
    assert panel_place(by_icon, as_qrect(laptop), work, size, None) == panel_place(
        by_icon, as_qrect(laptop), work, size
    )
    # control: no flyout open
    assert flyout_taken(icon, None, screens) is None


def test_the_tray_panel_leaves_the_flyout_free_on_every_taskbar_edge():
    from PySide6.QtCore import QRect, QSize

    from darbit.studio.tray import GAP, panel_place

    screen = QRect(0, 0, 1920, 1080)
    size = QSize(336, 324)
    # the taskbar on top: the flyout under it, the panel under the flyout
    work = QRect(0, 48, 1920, 1032)
    taken = QRect(1600, 56, 240, 120)
    spot = panel_place(QRect(1700, 80, 24, 24), screen, work, size, taken)
    assert spot.y() == 176 + GAP and work.contains(QRect(spot, size))
    # on the left: the panel to the right of the flyout
    work = QRect(48, 0, 1872, 1080)
    taken = QRect(56, 800, 120, 240)
    spot = panel_place(QRect(80, 900, 24, 24), screen, work, size, taken)
    assert spot.x() == 176 + GAP and work.contains(QRect(spot, size))
    # on the right: to the left of it
    work = QRect(0, 0, 1872, 1080)
    taken = QRect(1744, 800, 120, 240)
    spot = panel_place(QRect(1800, 900, 24, 24), screen, work, size, taken)
    panel = QRect(spot, size)
    assert panel.right() + 1 == 1744 - GAP and work.contains(panel) and not panel.intersects(taken)


def test_the_tray_flyout_is_none_where_the_system_has_none(monkeypatch):
    from darbit.platform import backend, system

    def none_here():
        raise backend.NotSupported("no tray here")

    monkeypatch.setattr(backend, "system", none_here)
    assert system.tray_flyout() is None


def test_the_tray_panel_lists_the_running_bots_and_says_what_quit_does(qt):
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.tray import TrayPanel

    panel_actions = TrayPanel()
    quits = []
    panel_actions.quitWanted.connect(lambda: quits.append(True))
    client = FakeClient()  # ad-bot runs, "other" is stopped
    studio = backend.Studio(lambda: client)
    engine = app.load(studio, tray_panel=panel_actions)
    root = engine.rootObjects()[0]
    studio.connect()
    wait_until(lambda: studio.bots)
    panel = root.findChild(QQuickWindow, "trayPanel")
    assert [bot["name"] for bot in panel.property("running")] == ["ad-bot"]  # the stopped one isn't listed
    assert studio.quitLabel == "Quit and stop ad-bot"
    studio.setKeepBots(True)
    assert studio.quitLabel == "Quit (bots go on)"
    studio.setKeepBots(False)
    from PySide6.QtTest import QTest

    panel.show()
    panel.requestActivate()
    wait_until(lambda: panel.isActive())
    QTest.keyClick(panel, QtCore.Qt.Key_Escape)
    assert not panel.isVisible()  # Esc closes it
    panel.show()
    panel.requestActivate()
    wait_until(lambda: panel.isActive())
    root.requestActivate()  # a click anywhere else
    wait_until(lambda: not panel.isVisible())
    panel.show()
    wait_until(lambda: panel.isVisible())
    quit_line = root.findChild(QtCore.QObject, "quitLine")
    assert quit_line.property("text") == "Quit and stop ad-bot"
    QMetaObject.invokeMethod(quit_line, "clicked")
    assert quits == [True] and not panel.isVisible()  # Quit goes to app.py, and the panel closes
    del engine


def test_the_tray_panel_controls_each_running_bot_by_its_own_folder(qt):
    client = FakeClient()
    studio = backend.Studio(lambda: client, bot="/bots/other")
    studio.connect()
    wait_until(lambda: studio.bot.get("name") == "other")
    studio.pauseBot("/bots/ad-bot")
    studio.stopBot("/bots/ad-bot")
    wait_until(lambda: ("bot.stop", {"bot": "/bots/ad-bot"}) in client.asked)
    assert ("bot.pause", {"bot": "/bots/ad-bot"}) in client.asked
    controls = [params["bot"] for method, params in client.asked if method in ("bot.pause", "bot.stop")]
    assert controls == ["/bots/ad-bot", "/bots/ad-bot"]  # control: the shown bot isn't touched


class OneAtATime(FakeClient):
    """The service's one input bot at a time (decision 0020): ad-bot runs and sends input, other is stopped and sends
    input too, watcher is stopped and sends none. A start in the way of a running input bot is refused unless it
    replaces it."""

    def __init__(self, doctor_problems=0):
        super().__init__()
        self.doctor_problems = doctor_problems
        self.bots = {
            "/bots/ad-bot": {**BOT, "input": True},
            "/bots/other": {**BOT, "path": "/bots/other", "name": "other", "status": "stopped", "since": None},
            "/bots/watcher": {
                **BOT,
                "path": "/bots/watcher",
                "name": "watcher",
                "status": "stopped",
                "since": None,
                "input": False,
            },
        }

    def call(self, method, **params):
        if method == "bots.list":
            self.asked.append((method, params))
            return [dict(bot) for bot in self.bots.values()]
        if method == "bot.doctor":
            self.asked.append((method, params))
            return {
                "checks": [{"name": "targets", "ok": False, "found": "1 not taken", "missing": ["A"]}],
                "problems": 1,
            }
        if method == "bot.stop":
            self.bots[params["bot"]]["status"] = "stopped"
        if method == "bot.start":
            self.asked.append((method, params))
            return self.start(params["bot"], bool(params.get("replace")))
        if method == "bot.action.play":
            self.asked.append((method, params))
            return self.play(params["name"], bool(params.get("replace")))
        return super().call(method, **params)

    def play(self, name, replace):
        """An action sends input from the service: refused while any bot that sends input runs, its own included."""
        from darbit.service.client import ServiceError

        in_the_way = [
            dict(bot) for bot in self.bots.values() if bot["status"] in ("running", "paused") and bot.get("input", True)
        ]
        if in_the_way and not replace:
            raise ServiceError("in the way", code="input_bot_running", detail={"running": in_the_way})
        for bot in in_the_way:
            self.bots[bot["path"]]["status"] = "stopped"
        return {"playing": True}

    def start(self, path, replace):
        from darbit.service.client import ServiceError

        bot = self.bots[path]
        in_the_way = [
            dict(other)
            for other in self.bots.values()
            if other["path"] != path and other["status"] in ("running", "paused") and other.get("input", True)
        ]
        if bot.get("input", True) and in_the_way:
            if not replace:
                raise ServiceError(
                    f"{in_the_way[0]['name']} is running and uses the mouse and keys too",
                    code="input_bot_running",
                    detail={"running": in_the_way},
                )
            for other in in_the_way:
                self.bots[other["path"]]["status"] = "stopped"
        bot["status"] = "running"
        bot["since"] = time.time()
        return {"status": "running"}


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _sheet_button(sheet, name):
    return next(item for item in _walk(sheet.property("contentItem")) if item.objectName() == name)


def _studio_showing(client, bot):
    studio = backend.Studio(lambda: client, bot=bot)
    engine = app.load(studio)
    root = engine.rootObjects()[0]
    wait_until(lambda: studio.bot.get("path") == bot)
    return studio, engine, root


def test_play_while_another_input_bot_runs_asks_to_stop_it_and_start_this_one(qt):
    from PySide6.QtCore import QObject

    client = OneAtATime()
    studio, engine, root = _studio_showing(client, "/bots/other")
    started = []
    studio.started.connect(lambda: started.append(True))
    sheet = root.findChild(QObject, "stopAndStartSheet")
    studio.start()
    wait_until(lambda: sheet.property("opened"))
    question = next(item for item in _walk(sheet.property("contentItem")) if item.objectName() == "question")
    assert question.property("text") == "ad-bot is running and uses the mouse and keys. Stop it and start other?"
    assert started == [] and studio.message == ""  # a question, not a failure
    QMetaObject.invokeMethod(_sheet_button(sheet, "stopAndStart"), "clicked")
    wait_until(lambda: started == [True])
    assert ("bot.start", {"bot": "/bots/other", "replace": True}) in client.asked
    wait_until(lambda: studio.bot.get("status") == "running")
    assert client.bots["/bots/ad-bot"]["status"] == "stopped"
    assert not sheet.property("visible") and studio.inTheWay == {}
    del engine


def test_cancel_leaves_the_running_bot_and_starts_nothing(qt):
    from PySide6.QtCore import QObject

    client = OneAtATime()
    studio, engine, root = _studio_showing(client, "/bots/other")
    sheet = root.findChild(QObject, "stopAndStartSheet")
    studio.start()
    wait_until(lambda: sheet.property("opened"))
    QMetaObject.invokeMethod(_sheet_button(sheet, "keepRunning"), "clicked")
    wait_until(lambda: not sheet.property("visible"))
    assert studio.inTheWay == {}
    studio.replaceAndStart()  # nothing asked any more: nothing to replace
    QtCore.QCoreApplication.processEvents()
    starts = [params for method, params in client.asked if method == "bot.start"]
    assert starts == [{"bot": "/bots/other"}]
    assert client.bots["/bots/ad-bot"]["status"] == "running" and client.bots["/bots/other"]["status"] == "stopped"
    del engine


def test_start_anyway_after_the_checks_asks_too(qt):
    from PySide6.QtCore import QObject

    client = OneAtATime()
    studio, engine, root = _studio_showing(client, "/bots/other")
    checks = root.findChild(QObject, "checksSheet")
    question = root.findChild(QObject, "stopAndStartSheet")
    studio.play()
    wait_until(lambda: checks.property("opened"))
    QMetaObject.invokeMethod(_sheet_button(checks, "startAnyway"), "clicked")
    wait_until(lambda: question.property("opened"))
    assert not checks.property("visible")
    del engine


def test_a_bot_that_sends_no_input_starts_alongside_without_asking(qt):
    from PySide6.QtCore import QObject

    client = OneAtATime()
    studio, engine, root = _studio_showing(client, "/bots/watcher")
    sheet = root.findChild(QObject, "stopAndStartSheet")
    asked = []
    studio.askedToReplace.connect(lambda: asked.append(True))
    started = []
    studio.started.connect(lambda: started.append(True))
    studio.start()
    wait_until(lambda: started == [True])
    wait_until(lambda: len(studio.running) == 2)
    assert asked == [] and not sheet.property("visible")
    assert [bot["name"] for bot in studio.running] == ["ad-bot", "watcher"]  # both run
    del engine


def test_the_run_pill_has_a_line_for_each_running_bot_with_its_own_controls(qt):
    from PySide6.QtCore import QObject
    from PySide6.QtQuick import QQuickWindow

    from darbit.studio.hiding import HidingPill

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        client = OneAtATime()
        client.bots["/bots/watcher"]["status"] = "running"
        hiding = HidingPill(watch=lambda on_move: lambda: None)
        studio = backend.Studio(lambda: client, bot="/bots/watcher")
        engine = app.load(studio, run_pill=hiding)
        root = engine.rootObjects()[0]
        wait_until(lambda: len(studio.running) == 2)
        hiding.open()
        window = root.findChild(QQuickWindow, "runPill")
        wait_until(window.isVisible)
        assert [bot["name"] for bot in window.property("others").toVariant()] == ["ad-bot"]
        lines = window.findChild(QObject, "otherLines")
        wait_until(lambda: lines.property("visible"))
        stop = next(item for item in _walk(lines) if item.objectName() == "otherStop")
        pause = next(item for item in _walk(lines) if item.objectName() == "otherPause")
        QMetaObject.invokeMethod(pause, "clicked")
        QMetaObject.invokeMethod(stop, "clicked")
        wait_until(lambda: ("bot.stop", {"bot": "/bots/ad-bot"}) in client.asked)
        controls = [params["bot"] for method, params in client.asked if method in ("bot.pause", "bot.stop")]
        assert controls == ["/bots/ad-bot", "/bots/ad-bot"]  # control: the shown bot isn't touched
        wait_until(lambda: not lines.property("visible"))  # ad-bot stopped: only the shown bot is left
        assert window.property("others").toVariant() == []
        hiding.close()
        del engine
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


def test_playing_an_action_while_a_bot_runs_asks_to_stop_it_and_play(qt):
    from PySide6.QtCore import QObject

    client = OneAtATime()
    studio, engine, root = _studio_showing(client, "/bots/other")
    sheet = root.findChild(QObject, "stopAndStartSheet")
    said = []
    studio.said.connect(said.append)
    studio.playAction("go_to_boss")
    wait_until(lambda: sheet.property("opened"))
    question = next(item for item in _walk(sheet.property("contentItem")) if item.objectName() == "question")
    assert question.property("text") == "ad-bot is running and uses the mouse and keys. Stop it and play go_to_boss?"
    assert said == []  # control: nothing played yet
    assert _sheet_button(sheet, "stopAndStart").property("text") == "Stop and play"
    QMetaObject.invokeMethod(_sheet_button(sheet, "stopAndStart"), "clicked")
    wait_until(
        lambda: ("bot.action.play", {"bot": "/bots/other", "name": "go_to_boss", "replace": True}) in client.asked
    )
    wait_until(lambda: len(said) == 1)  # played: the Studio says so, as without a question
    assert client.bots["/bots/ad-bot"]["status"] == "stopped"
    del engine


def test_recording_refused_while_a_bot_runs_says_why_and_brings_the_studio_back(qt):
    class Recorder(QtCore.QObject):
        finished = QtCore.Signal(str)
        pictureWanted = QtCore.Signal(str, bool)
        active = False

        def start(self, folder, name, again):
            return "ad-bot is running and uses the mouse and keys too: stop it to record dim_run"

    class Capture(QtCore.QObject):
        saved = QtCore.Signal(str)

    studio = backend.Studio(lambda: OneAtATime())
    window = Window()
    app._connect_recorder(studio, Capture(), Recorder(), window)
    said = []
    studio.said.connect(said.append)
    studio.recordWanted.emit("/bots/other", "dim_run", False)
    assert not window.shown  # the Studio steps aside first
    wait_until(lambda: said == ["ad-bot is running and uses the mouse and keys too: stop it to record dim_run"])
    assert window.shown


def test_motion_is_instant_with_effects_off_or_the_window_out_of_sight(qt):
    assert theme.motion(True)["rise"] == theme.DURATIONS["rise"]
    assert theme.motion(False)["rise"] == 0
    assert theme.motion(False)["spring"] == [0.34, 1.4, 0.64, 1, 1, 1]  # a curve stays a curve
    studio = backend.Studio(FakeClient)  # effects off: the qt fixture's
    assert not studio.motion["on"]
    assert studio.motion["count"] == 0
    studio.setEffects(True)
    assert studio.motion["on"]
    assert studio.motion["count"] == theme.DURATIONS["count"]
    studio.setShown(False)  # hidden behind the run pill, or minimized
    assert not studio.motion["on"]
    assert studio.motion["count"] == 0
    assert studio.pillMotion["on"]  # the pills show while the Studio is hidden


def test_blur_through_and_the_aurora_are_off_until_turned_on_and_kept(qt):
    studio = backend.Studio(FakeClient)
    assert (studio.blurThrough, studio.aurora) == (False, False)
    studio.setBlurThrough(True)
    studio.setAurora(True)
    assert (studio.blurThrough, studio.aurora) == (True, True)
    assert (backend.Studio(FakeClient).blurThrough, backend.Studio(FakeClient).aurora) == (True, True)


def test_the_battery_is_asked_about_only_while_the_aurora_could_show(qt, monkeypatch):
    asked = []

    def on_battery():
        asked.append(True)
        return True

    monkeypatch.setattr(backend.system, "on_battery", on_battery)
    studio = backend.Studio(FakeClient)
    assert not studio.onBattery
    assert asked == []  # the aurora is off: nobody asks
    studio.setAurora(True)
    assert studio.onBattery  # so the aurora rests
    studio.setShown(False)
    assert not studio._battery_check.isActive()
    studio.setShown(True)
    assert studio._battery_check.isActive()
    studio.setAurora(False)
    assert not studio._battery_check.isActive()


def test_out_of_sight_the_overview_waits_but_the_run_pill_and_the_tray_still_hear(qt, monkeypatch):
    client = FakeClient()
    studio = backend.Studio(lambda: client)
    told = []
    studio.pictureFailing.connect(lambda title, text: told.append(title))
    studio.connect()
    wait_until(lambda: len(studio.overview.get("layout", [])) == 8)
    assert studio.live["now"]["path"] == ["Speed Raid", "Sakura"]
    studio.setShown(False)
    answer = _overview_answer()
    failing = {"target": "Team.Card", "since": "2026-11-06T01:15:08.977", "count": 2, "sentence": "AFK failed."}
    answer["data"] = {**answer["data"], "now": {"path": ["AFK"], "since": None}, "failing": failing}
    monkeypatch.setitem(ANSWERS, "bot.overview", answer)
    client.listener("project.changed", {"path": "/bots/ad-bot"})
    wait_until(lambda: studio.live["now"]["path"] == ["AFK"])  # the run pill's line
    assert told == ["ad-bot: Team.Card may have stopped matching"]  # the tray's warning
    assert studio.overview["data"]["now"]["path"] == ["Speed Raid", "Sakura"]  # the page waits
    studio.setShown(True)
    assert studio.overview["data"]["now"]["path"] == ["AFK"]


def test_the_overview_keeps_its_blocks_when_new_numbers_come(qt):
    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]

    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    def blocks():
        return [item for item in walk(window.contentItem()) if item.metaObject().className().startswith("Block_")]

    wait_until(lambda: len(blocks()) == 8)
    before = set(blocks())
    studio.loadOverview()
    studio.loadOverview()
    wait_until(lambda: not studio.busy)
    QtCore.QCoreApplication.processEvents()
    assert set(blocks()) == before  # the same blocks, given their new numbers: nothing is made again
    del engine


def test_the_pages_draw_with_blur_through_and_the_aurora_without_a_qml_warning(effects, tmp_path):
    settings = {"studio.effects": True, "studio.blur_through": True, "studio.aurora": True, "studio.picker": "sidebar"}
    (tmp_path / "config" / "ui.json").write_text(json.dumps(settings), encoding="utf-8")
    warnings = []

    def keep(kind, context, text):
        if kind != QtCore.QtMsgType.QtDebugMsg and ".qml" in text:
            warnings.append(text)

    QtCore.qInstallMessageHandler(keep)
    try:
        for page in ("overview", "library"):
            picture = tmp_path / f"{page}.png"
            app.shot(picture, page, "glass-dark", (1200, 800), connect=FakeClient)
            assert picture.stat().st_size > 10_000
    finally:
        QtCore.qInstallMessageHandler(None)
    assert warnings == []


MODES = [{"name": "Speed Raid", "steps": ["open the list", "pick a character"]}, {"name": "Raid", "steps": []}]


class WithModes(OneAtATime):
    """other declares modes; a bot started for one says so in bots.list, as the service does."""

    def __init__(self):
        super().__init__()
        self.bots["/bots/other"]["modes"] = MODES

    def start(self, path, replace):
        answer = super().start(path, replace)
        self.bots[path]["only"] = self.asked[-1][1].get("only")
        return answer


def _palette_labels(palette):
    found = palette.property("shown")
    found = found.toVariant() if hasattr(found, "toVariant") else found
    return [one["label"] for one in found]


def test_the_palette_lists_each_mode_and_step_the_bot_declares_to_run_alone(qt):
    from PySide6.QtCore import QObject

    client = WithModes()
    studio, engine, root = _studio_showing(client, "/bots/other")
    palette = root.findChild(QObject, "commandPalette")
    QMetaObject.invokeMethod(palette, "open")
    wait_until(lambda: palette.property("visible"))
    search = root.findChild(QObject, "paletteSearch")
    search.setProperty("text", "run")
    wait_until(
        lambda: (
            _palette_labels(palette)
            == [
                "Run only Speed Raid",
                "Run step: Speed Raid · open the list",
                "Run step: Speed Raid · pick a character",
                "Run only Raid",
            ]
        )
    )
    search.setProperty("text", "run step pick")
    wait_until(lambda: _palette_labels(palette) == ["Run step: Speed Raid · pick a character"])
    QMetaObject.invokeMethod(palette, "runAt", Q_ARG("QVariant", 0))
    checks = root.findChild(QObject, "checksSheet")
    wait_until(lambda: checks.property("opened"))  # Play's checks first, as for a round
    QMetaObject.invokeMethod(_sheet_button(checks, "startAnyway"), "clicked")
    only = {"mode": "Speed Raid", "step": "pick a character"}
    wait_until(lambda: ("bot.start", {"bot": "/bots/other", "only": only}) in client.asked)
    studio.selectBot("/bots/ad-bot")  # running, and declares nothing: nothing to run alone
    QMetaObject.invokeMethod(palette, "open")
    search.setProperty("text", "run")
    wait_until(lambda: palette.property("visible"))
    assert not any(label.startswith("Run ") for label in _palette_labels(palette))
    del engine


def test_one_mode_asks_to_stop_the_bot_in_the_way_and_shows_only_while_it_runs(qt):
    from PySide6.QtCore import QObject

    client = WithModes()
    studio, engine, root = _studio_showing(client, "/bots/other")
    checks = root.findChild(QObject, "checksSheet")
    question = root.findChild(QObject, "stopAndStartSheet")
    label = root.findChild(QObject, "runOnlyLabel")
    studio.playOnly("Speed Raid", "")
    wait_until(lambda: checks.property("opened"))
    QMetaObject.invokeMethod(_sheet_button(checks, "startAnyway"), "clicked")
    wait_until(lambda: question.property("opened"))  # ad-bot runs and sends input (decision 0020)
    QMetaObject.invokeMethod(_sheet_button(question, "stopAndStart"), "clicked")
    only = {"mode": "Speed Raid"}
    wait_until(lambda: ("bot.start", {"bot": "/bots/other", "only": only, "replace": True}) in client.asked)
    wait_until(lambda: studio.bot.get("status") == "running")
    assert client.bots["/bots/ad-bot"]["status"] == "stopped"
    wait_until(lambda: label.property("visible"))
    assert label.property("text") == "only Speed Raid"
    del engine


def test_a_round_rows_play_runs_that_mode_alone_while_the_bot_is_stopped(qt):
    from PySide6.QtCore import QObject

    client = WithModes()
    studio, engine, root = _studio_showing(client, "/bots/other")
    root.resize(1400, 880)
    studio.loadOverview()

    def buttons():
        return [item for item in _walk(root.contentItem()) if item.objectName() == "runOnly"]

    def rows():
        found = {}
        for button in buttons():
            row = button.parentItem().parentItem()
            step = row.property("modelData")
            step = step.toVariant() if hasattr(step, "toVariant") else step
            found[step["name"]] = row
        return found

    wait_until(lambda: len(buttons()) == 3)
    # ▶ shows on hover only for a mode the bot declares (Raid, Speed Raid), not for AFK, and never at rest
    assert {name: row.property("runnable") for name, row in rows().items()} == {
        "Raid": True,
        "Speed Raid": True,
        "AFK": False,
    }
    assert not any(button.property("visible") for button in buttons())
    speed_raid = next(button for button in buttons() if button.parentItem().parentItem() == rows()["Speed Raid"])
    QMetaObject.invokeMethod(speed_raid, "clicked")
    checks = root.findChild(QObject, "checksSheet")
    wait_until(lambda: checks.property("opened"))  # Play's checks first, as for a round
    QMetaObject.invokeMethod(_sheet_button(checks, "startAnyway"), "clicked")
    wait_until(lambda: any(params.get("only") == {"mode": "Speed Raid"} for _, params in client.asked))
    client.bots["/bots/other"]["status"] = "running"
    studio.connect()  # bots.list again: other runs now
    wait_until(lambda: studio.bot.get("status") == "running")
    wait_until(lambda: not any(row.property("runnable") for row in rows().values()))
    del engine


def test_what_the_bot_sees_boxes_its_last_look_and_is_followed_only_in_sight(qt, monkeypatch, tmp_path):
    import cv2
    import numpy as np

    from darbit import paths
    from darbit.runtime import sees

    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path / "data")
    logs = tmp_path / "logs"
    logs.mkdir()
    cv2.imwrite(str(logs / "sees-1.jpg"), np.zeros((360, 640, 3), np.uint8))
    look = {
        "time": "2026-11-09T08:00:14.250",
        "kind": "wait",
        "targets": ["Play.Raid.png", "Dim.Tab.Create.png"],
        "found": "Play.Raid.png",
        "file": "sees-1.jpg",
        "w": 640,
        "h": 360,
        "boxes": [
            {"name": "Dim.Tab.Create.png", "x": 600, "y": 10, "w": 20, "h": 20, "score": 0.41, "found": False},
            {"name": "Play.Raid.png", "x": 180, "y": 60, "w": 90, "h": 200, "score": 1.0, "found": True},
        ],
    }
    (logs / sees.LOOK).write_text(json.dumps(look), encoding="utf-8")
    answer = _overview_answer()
    answer["layout"] = [{"kind": "sees", "shows": "sees", "title": "What the bot sees", "width": 8, "origin": "darbit"}]
    answer["data"]["sees"] = {"look": str(logs / sees.LOOK), "logs": str(logs)}
    monkeypatch.setitem(ANSWERS, "bot.overview", answer)
    studio = backend.Studio(FakeClient)
    engine = app.load(studio)
    window = engine.rootObjects()[0]

    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    def texts():
        return [item.property("text") for item in walk(window.contentItem()) if item.property("text")]

    wait_until(lambda: "Play.Raid 1.00" in texts())  # found: its name and score on its box
    assert "live · 08:00:14" in texts()
    assert "Play.Raid, Dim.Tab.Create → found Play.Raid" in texts()
    dashed = [item for item in walk(window.contentItem()) if item.metaObject().className().startswith("Dashed")]
    assert len([item for item in dashed if item.isVisible()]) == 1  # not found: dashed at its closest spot
    assert json.loads(sees.watching_file().read_text(encoding="utf-8")) == {"logs": str(logs)}
    studio.setShown(False)  # hidden or minimized: the bot stops keeping pictures
    QtCore.QCoreApplication.processEvents()
    assert not sees.watching_file().exists()
    del engine
