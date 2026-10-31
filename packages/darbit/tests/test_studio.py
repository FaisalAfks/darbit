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
    studio.loadLibrary()
    studio.loadDays()
    studio.loadSettings()
    wait_until(lambda: studio.library and studio.days and studio.settings)
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
@pytest.mark.parametrize("page", ["overview", "library", "runs", "settings"])
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
