"""darbit's service: its messages, the token, and bots started, paused and stopped by a client over the socket."""

import threading
import time

import pytest
from test_hub import bot  # noqa: F401 - the fixture: a small bot in a temporary bots folder

from darbit import events, paths
from darbit.service import client, protocol
from darbit.service.host import Service, address_file


def test_messages_go_and_come_back_the_same():
    for message in (
        protocol.Hello("t0k", "test"),
        protocol.Request(3, "bot.start", {"bot": "tick-bot"}),
        protocol.Reply(3, {"status": "running"}),
        protocol.Reply(4, error="no bot called x"),
        protocol.Event("bot.status", {"status": "paused"}),
    ):
        line = protocol.encode(message)
        assert line.endswith(b"\n")
        assert protocol.decode(line) == message


@pytest.mark.parametrize("line", [b"not json", b"[1, 2]", b'{"type": "shout"}', b'{"type": "request", "x": 1}'])
def test_lines_that_arent_messages_are_refused(line):
    with pytest.raises(protocol.ProtocolError):
        protocol.decode(line)


@pytest.fixture
def service(tmp_path, monkeypatch):
    """A service on a free port, with its address file in a temporary data folder."""

    def data_dir():
        return tmp_path / "data"

    monkeypatch.setattr(paths, "data_dir", data_dir)
    running = Service()
    thread = threading.Thread(target=running.serve_forever, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not address_file().exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    yield running
    running.shutdown()
    thread.join(5)


def test_a_client_with_the_token_is_answered(service):
    with client.Client("test") as connection:
        pong = connection.call("service.ping")
    assert pong["version"] == protocol.VERSION
    assert "bot.start" in pong["methods"]
    assert client.running()


def test_a_wrong_token_is_turned_away(service, tmp_path):
    fake = tmp_path / "fake.json"
    fake.write_text(f'{{"port": {service.port}, "token": "guess"}}', encoding="utf-8")
    with pytest.raises(client.ServiceError, match="wrong token"):
        client.Client("test", fake)


def test_no_service_is_said_plainly(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path / "nothing")
    with pytest.raises(client.NotRunning, match="darbit serve"):
        client.Client("test")
    assert not client.running()


def test_refused_requests_come_back_as_errors(service):
    with client.Client("test") as connection:
        with pytest.raises(client.ServiceError, match="no method called"):
            connection.call("bot.fly")
        with pytest.raises(client.ServiceError, match="needs `bot`"):
            connection.call("bot.start")
        with pytest.raises(client.ServiceError, match="no bot called"):
            connection.call("bot.start", bot="nobody")


def test_events_reach_every_client(service):
    seen = []
    with client.Client("test") as connection:
        connection.on_event(lambda topic, data: seen.append((topic, data)))
        connection.call("service.ping")  # the connection is set up on the service's side
        events.publish("bot.status", {"status": "paused"})
        deadline = time.monotonic() + 5
        while not seen and time.monotonic() < deadline:
            time.sleep(0.01)
    assert seen == [("bot.status", {"status": "paused"})]


def test_a_bot_is_started_paused_and_stopped_through_the_service(service, bot):  # noqa: F811
    with client.Client("test") as connection:
        assert [found["name"] for found in connection.call("bots.list")] == ["tick-bot"]
        assert connection.call("bot.start", bot="tick-bot") == {"status": "running"}
        assert connection.call("bot.status", bot="tick-bot")["status"] == "running"
        assert connection.call("bot.pause", bot="tick-bot") == {"status": "paused"}
        assert connection.call("bot.pause", bot=str(bot)) == {"status": "running"}  # a path works too
        time.sleep(0.5)
        assert connection.call("bot.stop", bot="tick-bot") == {"status": "stopped"}
        assert connection.call("bot.status", bot="tick-bot")["status"] == "stopped"


def test_service_stop_ends_it(service):
    with client.Client("test") as connection:
        assert connection.call("service.stop") == {"stopping": True}
    deadline = time.monotonic() + 5
    while address_file().exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not address_file().exists()


def test_the_cli_talks_to_the_service(service, bot, capsys):  # noqa: F811
    from darbit import cli

    assert cli.main(["bots"]) == 0
    assert "tick-bot" in capsys.readouterr().out
    assert cli.main(["status", "tick-bot"]) == 0
    assert capsys.readouterr().out.strip() == "tick-bot: stopped"
    assert cli.main(["start", "nobody"]) == 1
    assert "no bot called nobody" in capsys.readouterr().out


def test_history_shows_a_day(service, bot, capsys):  # noqa: F811
    from darbit import cli

    logs = bot / ".darbit" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "report-2026-10-31.jsonl").write_text(
        '{"time": "2026-10-31T09:00:00.000", "event": "gain", "name": "Gems", "amount": 40, "total": 900}\n'
        '{"time": "2026-10-31T10:30:00.000", "event": "gain", "name": "Gems", "amount": 20}\n',
        encoding="utf-8",
    )
    assert cli.main(["history", "tick-bot"]) == 0
    out = capsys.readouterr().out
    assert "2026-10-31, 9:00:00 to 10:30:00" in out
    assert "gained 60 Gems (total 900)" in out
    assert cli.main(["history", "tick-bot", "--days"]) == 0
    assert "1:30:00" in capsys.readouterr().out
