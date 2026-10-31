"""Notifications: the settings file, each channel's message, and what the service tells about (a failure, a stuck
bot, the day's summary), sent to a local HTTP server standing in for the phone."""

import http.server
import json
import threading
import time
from datetime import datetime

import pytest

from darbit.service import notify


@pytest.fixture
def phone():
    """A local server that keeps every message posted to it."""
    got = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            size = int(self.headers["Content-Length"])
            got.append((self.path, self.headers["Content-Type"], self.rfile.read(size).decode()))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            return None

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}", got
    server.shutdown()


def wait_for(got, count):
    deadline = time.monotonic() + 5
    while len(got) < count and time.monotonic() < deadline:
        time.sleep(0.01)


def test_settings_name_each_channel(tmp_path):
    path = tmp_path / "notify.toml"
    path.write_text(
        '[ntfy]\ntopic = "me"\n[discord]\nwebhook = "https://d/x"\n[telegram]\ntoken = "1:A"\nchat = "7"\n'
        '[when]\nended = true\nstuck_minutes = 5\nsummary = ""\n',
        encoding="utf-8",
    )
    settings = notify.load_settings(path)
    assert [channel.name for channel in settings.channels] == ["ntfy", "discord", "telegram"]
    assert settings.channels[0].url == "https://ntfy.sh/me"
    assert settings.channels[2].url == "https://api.telegram.org/bot1:A/sendMessage"
    assert (settings.failed, settings.ended, settings.stuck_minutes, settings.summary) == (True, True, 5, "")
    assert json.loads(settings.channels[2].body("T", "x")[0]) == {"chat_id": "7", "text": "T\nx"}
    assert notify.load_settings(tmp_path / "missing.toml").channels == []


def test_each_channel_gets_its_own_message(tmp_path, phone):
    url, got = phone
    path = tmp_path / "notify.toml"
    path.write_text(f'[ntfy]\nserver = "{url}"\ntopic = "me"\n[discord]\nwebhook = "{url}/hook"\n', encoding="utf-8")
    for channel in notify.load_settings(path).channels:
        assert notify.post(channel, "darbit", "hello")
    assert got[0] == ("/me", "text/plain; charset=utf-8", "darbit\nhello")
    assert got[1][0] == "/hook"
    assert json.loads(got[1][2]) == {"content": "**darbit**\nhello"}
    unreachable = notify.Channel("ntfy", "http://127.0.0.1:9/x", notify._ntfy_body)
    assert not notify.post(unreachable, "darbit", "hello")


def test_a_failed_bot_is_told_and_a_stopped_one_only_when_asked(phone, monkeypatch):
    url, got = phone
    settings = notify.Settings([notify.Channel("ntfy", f"{url}/me", notify._ntfy_body)])
    monkeypatch.setattr(notify, "_name", lambda folder: "fish-bot")
    monkeypatch.setattr(notify, "_last_problem", lambda folder: "Fish: the rod wasn't found")
    notifier = notify.Notifier(settings)
    notifier.on_event("project.status", {"path": "/bots/fish", "status": "stopped"})
    notifier.on_event("project.status", {"path": "/bots/fish", "status": "failed"})
    wait_for(got, 1)
    time.sleep(0.1)
    assert [body for _, _, body in got] == ["fish-bot failed\nFish: the rod wasn't found"]


def test_a_quiet_running_bot_is_told_once_and_the_summary_once_a_day(phone, monkeypatch, tmp_path):
    url, got = phone
    settings = notify.Settings([notify.Channel("ntfy", f"{url}/me", notify._ntfy_body)], stuck_minutes=1)
    monkeypatch.setattr(notify.hub, "running", lambda: [tmp_path / "fish-bot"])
    monkeypatch.setattr(notify, "summary", lambda day: f"fish-bot\ngained 3 Fish on {day}")
    notifier = notify.Notifier(settings)
    notifier.last_change[str(tmp_path / "fish-bot")] = time.monotonic() - 120
    notifier.look_now(datetime(2026, 10, 31, 12, 0))  # before the summary's time
    notifier.look_now(datetime(2026, 10, 31, 23, 45))
    notifier.look_now(datetime(2026, 10, 31, 23, 50))  # both already told
    wait_for(got, 2)
    time.sleep(0.1)
    bodies = sorted(body for _, _, body in got)
    assert bodies == [
        "darbit, 2026-10-31\nfish-bot\ngained 3 Fish on 2026-10-31",
        "fish-bot may be stuck\nnothing in its report for 1 minutes",
    ]
