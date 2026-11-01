"""darbit Studio: its theme tokens, what its pages bind to, and every page drawn offscreen with no QML warning.

Needs the studio extra (PySide6); skipped without it. The service is a fake client with canned answers.
"""

import os
import time

import pytest

from darbit.studio import theme

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtCore = pytest.importorskip("PySide6.QtCore", exc_type=ImportError)

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
    wait_until(lambda: len(studio.overview) == 6)
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
    assert capture.save("", "image", box, None, None)["error"] == "give it a name"
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
        wait_until(lambda: len(window.property("matches") or []) == 1)
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
    from darbit.studio.runpill import HIDE_AFTER, Peek

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
    from darbit.studio.runpill import RunPill

    moves = []
    client = Runs()
    studio = backend.Studio(lambda: client)
    pill = RunPill(watch=lambda on_move: moves.append(on_move) or (lambda: moves.remove(on_move)))
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

    from darbit.studio.runpill import RunPill

    warnings = []
    QtCore.qInstallMessageHandler(lambda kind, context, text: warnings.append(text) if ".qml" in text else None)
    try:
        pill = RunPill(watch=lambda on_move: None)
        studio = backend.Studio(FakeClient)
        engine = app.load(studio, run_pill=pill)
        root = engine.rootObjects()[0]  # held, or Qt deletes it
        studio.connect()
        wait_until(lambda: studio.bot.get("name") == "ad-bot")
        studio.loadOverview()
        wait_until(lambda: len(studio.overview) == 6)
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
