"""The in-process event bus: the runtime publishes its log and report lines; nobody listening costs nothing."""

from darbit import events


def test_events_reach_listeners_and_a_broken_one_is_skipped():
    got = []

    def broken(topic, data):
        raise ZeroDivisionError

    def remember(topic, data):
        got.append((topic, data))

    stop_broken = events.listen(broken)
    stop = events.listen(remember)
    events.publish("log", {"line": "hi"})
    stop()
    stop_broken()
    events.publish("log", {"line": "nobody"})
    assert got == [("log", {"line": "hi"})]


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
