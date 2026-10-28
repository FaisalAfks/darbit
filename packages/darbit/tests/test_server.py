"""The local server: requests and replies, events, tokens and origins, frames, and a real server on a port."""

import json
import time
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("starlette")  # the server needs the `app` extra; the dev environment has it

from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from darbit import events, paths
from darbit.server import app as server_app
from darbit.server import frames, protocol

TOKEN = "test-token"


@pytest.fixture(autouse=True)
def own_folders(tmp_path, monkeypatch):
    """Settings and server.json in a temporary folder, never the real AppData."""

    def config_dir():
        return tmp_path / "config"

    def data_dir():
        return tmp_path / "data"

    monkeypatch.setattr(paths, "config_dir", config_dir)
    monkeypatch.setattr(paths, "data_dir", data_dir)


@pytest.fixture
def client():
    return TestClient(server_app.create_app(TOKEN, 8123))


def ask(socket, kind: str, data: dict | None = None, request: int = 1, passed: list | None = None) -> dict:
    """Send a request and wait for its reply; events that arrive first go into `passed`."""
    socket.send_text(json.dumps({"type": kind, "id": request, "data": data or {}}))
    while True:
        message = socket.receive_json()
        if message.get("type") == "reply" and message.get("id") == request:
            return message
        if passed is not None:
            passed.append(message)


def test_a_request_gets_its_reply(client):
    with client.websocket_connect(f"/ws?token={TOKEN}") as socket:
        reply = ask(socket, "ping")
    assert reply["error"] is None
    assert "darbit" in reply["data"]


def test_unknown_requests_and_failing_handlers_reply_with_the_reason(client, monkeypatch):
    def broken(data):
        raise ValueError("no screen to grab")

    monkeypatch.setitem(server_app.HANDLERS, "capture.freeze", broken)
    with client.websocket_connect(f"/ws?token={TOKEN}") as socket:
        assert "unknown request" in ask(socket, "fly", request=1)["error"]
        assert ask(socket, "capture.freeze", request=2)["error"] == "no screen to grab"
        assert ask(socket, "ping", request=3)["error"] is None  # the connection keeps working


def test_events_reach_every_window(client):
    with (
        client.websocket_connect(f"/ws?token={TOKEN}") as first,
        client.websocket_connect(f"/ws?token={TOKEN}") as second,
    ):
        ask(first, "ping")
        ask(second, "ping")  # both are listening once they've answered
        events.publish("log", {"line": "found Gui.Play", "time": "12:00:00"})
        assert first.receive_json() == {"type": "log", "data": {"line": "found Gui.Play", "time": "12:00:00"}}
        assert second.receive_json()["data"]["line"] == "found Gui.Play"


def test_a_wrong_token_is_refused(client):
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws?token=guess") as socket:
        socket.receive_text()


@pytest.mark.parametrize(
    ("origin", "allowed"),
    [
        (None, True),
        ("http://127.0.0.1:8123", True),
        ("http://127.0.0.1:5173", True),
        ("vscode-webview://abc", True),
        ("https://evil.example", False),
        ("http://127.0.0.1:9999", False),
    ],
)
def test_origins(origin, allowed):
    assert server_app.origin_allowed(origin, 8123) is allowed


def test_a_foreign_page_is_refused(client):
    headers = {"origin": "https://evil.example"}
    with pytest.raises(WebSocketDisconnect), client.websocket_connect(f"/ws?token={TOKEN}", headers=headers) as socket:
        socket.receive_text()


def test_a_frame_arrives_with_its_exact_pixels(client, monkeypatch):
    pixels = np.random.default_rng(3).integers(0, 255, (60, 80, 3), dtype=np.uint8)

    def freeze(data):
        return frames.encode(pixels, {"monitor": 1})

    monkeypatch.setitem(server_app.HANDLERS, "capture.freeze", freeze)
    with client.websocket_connect(f"/ws?token={TOKEN}") as socket:
        socket.send_text(json.dumps({"type": "capture.freeze", "id": 9, "data": {}}))
        header, data = frames.unpack(socket.receive_bytes())
        reply = socket.receive_json()
    assert header == {"type": "frame", "id": 9, "w": 80, "h": 60, "format": "rgba", "monitor": 1}
    assert reply["data"] == {"frame": True, "w": 80, "h": 60}
    assert len(data) == 80 * 60 * 4
    assert np.array_equal(frames.decode(header, data), pixels)  # exact pixels


def test_small_images_go_as_png():
    pixels = np.random.default_rng(4).integers(0, 255, (20, 30, 3), dtype=np.uint8)
    frame = frames.encode(pixels, format="png")
    header, data = frames.unpack(frames.pack(frame.header(None), frame.data))
    assert header["format"] == "png"
    assert np.array_equal(frames.decode(header, data), pixels)


def test_choosing_a_theme_tells_every_window(client, tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "theme.toml").write_text('base = "midnight"\naccent = "#ff7ab6"\n', encoding="utf-8")
    with client.websocket_connect(f"/ws?token={TOKEN}") as socket:
        passed = []
        assert ask(socket, "settings.set", {"key": "ui.theme", "value": "glass-light"}, 1, passed)["error"] is None
        changed = passed[0] if passed else socket.receive_json()  # the event can come before or after the reply
        assert changed["type"] == "theme.changed"
        assert changed["data"] == {"name": "midnight", "tokens": {"accent": "#ff7ab6"}}  # the custom theme's base wins
        assert ask(socket, "settings.get", {"key": "ui.theme"}, 2)["data"] == "glass-light"


def test_http_routes_need_the_token(client):
    assert client.get("/ping").status_code == 401
    assert client.get("/ping", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200
    assert client.get(f"/keymap?token={TOKEN}").json()["global"]


def test_the_runtime_publishes_its_log_and_report(monkeypatch):
    from darbit.runtime import log
    from darbit.settings import settings

    monkeypatch.setattr(settings, "log", False)  # no files; events still go out
    seen = []

    def remember(topic, data):
        seen.append((topic, data))

    stop = events.listen(remember)
    try:
        log.log("found Gui.Play")
        log.record("step", step="Raid", state="started")
    finally:
        stop()
    assert seen[0][0] == "log" and seen[0][1]["line"] == "found Gui.Play"
    assert seen[1][0] == "record" and seen[1][1]["fields"]["step"] == "Raid"


def test_publishing_with_nobody_listening_does_nothing():
    events.publish("log", {"line": "nobody hears this"})


def test_the_typescript_types_match_the_protocol():
    generated = protocol.typescript()
    file = Path(__file__).parents[2] / "ui" / "src" / "lib" / "protocol.ts"
    assert file.read_text(encoding="utf-8") == generated, "run: uv run python -m darbit.server.protocol --ts"


def test_a_real_server_starts_once_and_answers():
    websockets = pytest.importorskip("websockets.sync.client")
    from darbit import server

    first = server.serve()
    try:
        assert server.running() == first
        assert server.serve() == first  # a second start reuses it
        with websockets.connect(f"ws://127.0.0.1:{first.port}/ws?token={first.token}") as socket:
            socket.send(json.dumps({"type": "ping", "id": 1, "data": {}}))
            assert json.loads(socket.recv(timeout=5))["error"] is None
            started = time.perf_counter()
            events.publish("log", {"line": "hello", "time": "12:00:00"})
            assert json.loads(socket.recv(timeout=5))["data"]["line"] == "hello"
            assert time.perf_counter() - started < 0.5
    finally:
        server.stop()
    assert server.running() is None
    assert not server.info_file().exists()


def test_a_second_darbit_app_brings_the_open_studio_forward(client, monkeypatch):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    monkeypatch.delitem(server_app.HANDLERS, "studio.show", raising=False)
    assert client.get("/studio", headers=headers).json() == {"shown": False}  # no Studio here: open one

    shown = []
    monkeypatch.setitem(server_app.HANDLERS, "studio.show", shown.append)
    assert client.get("/studio", headers=headers).json() == {"shown": True}
    assert shown == [{}]
    assert client.get("/studio").status_code == 401
