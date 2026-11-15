"""apps.open logs what it opened without the parts that can hold a secret (#495)."""

from darbit.runtime import apps


def test_a_link_stops_at_its_query_fragment_or_first_parameter():
    assert apps.shown("https://example.com/share?code=SECRET&type=Server") == "https://example.com/share…"
    assert apps.shown("https://example.com/page#token=SECRET") == "https://example.com/page…"
    assert apps.shown("game://placeId=123&linkCode=SECRET") == "game://placeId=123…"
    assert apps.shown("https://example.com/plain/path") == "https://example.com/plain/path"  # nothing to hide


def test_a_link_never_shows_a_user_and_password():
    assert apps.shown("https://user:pass@example.com/x") == "https://example.com/x…"


def test_a_path_shows_only_the_programs_name():
    assert apps.shown(r"C:\Users\someone\Apps\Tool\tool.exe") == "tool.exe"
    assert apps.shown("notepad.exe") == "notepad.exe"


def test_open_logs_the_shown_link(monkeypatch):
    launched, lines = [], []
    monkeypatch.setattr(apps.windows, "launch", launched.append)
    monkeypatch.setattr(apps, "log", lines.append)
    apps.open("https://example.com/share?code=SECRET")
    assert launched == ["https://example.com/share?code=SECRET"]  # opened as given
    assert lines == ["open https://example.com/share…"]
    assert "SECRET" not in lines[0]
