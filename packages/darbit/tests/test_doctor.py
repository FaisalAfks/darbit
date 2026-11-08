"""darbit doctor: a bot's readiness, checked from its files and this system, each check with its fix."""

import json

from darbit import cli, doctor
from darbit.platform.backend import NotSupported


def bot(tmp_path, window=""):
    folder = tmp_path / "doc-bot"
    (folder / "images").mkdir(parents=True)
    line = f'window = "{window}"\n' if window else ""
    (folder / "darbit.toml").write_text(f'[bot]\nname = "doc-bot"\n{line}', encoding="utf-8")
    (folder / "guide.toml").write_text(
        '[[screen]]\nname = "Lobby"\n  [[screen.take]]\n  image = "Lobby.Play"\n'
        '  [[screen.take]]\n  location = "Lobby.Spot"\n',
        encoding="utf-8",
    )
    return folder


def checks_of(folder):
    return {check.name: check for check in doctor.run(folder)}


def test_targets_not_taken_are_named_listed_and_fail_the_check(tmp_path, capsys):
    folder = bot(tmp_path)
    (folder / "images" / "Lobby.Spot.json").write_text(json.dumps({"location": [1, 2]}), encoding="utf-8")
    checks = checks_of(folder)
    assert checks["darbit.toml"].ok is True and checks["darbit.toml"].fix == ""
    targets = checks["targets"]
    assert targets.ok is False and targets.found == "1 of 2 not taken: Lobby.Play"
    assert targets.missing == ["Lobby.Play"]  # a Location saved as json counts as taken
    assert "Capture" in targets.fix
    assert checks["game window"].ok is None and checks["game window"].fix == ""  # none named
    assert cli.main(["doctor", str(folder)]) == 1
    out = capsys.readouterr().out
    assert "!!  targets: 1 of 2 not taken: Lobby.Play\n    fix: take them with Capture" in out
    assert "--  game window: darbit.toml names none\n" in out  # no fix line under a note


def test_every_target_taken_has_no_fix(tmp_path):
    folder = bot(tmp_path)
    (folder / "images" / "Lobby.Spot.json").write_text(json.dumps({"location": [1, 2]}), encoding="utf-8")
    (folder / "images" / "Lobby.Play.png").write_bytes(b"")
    targets = checks_of(folder)["targets"]
    assert targets.ok is True and targets.fix == "" and targets.missing == []


def test_missing_lists_every_target_while_found_counts_the_rest(tmp_path):
    folder = bot(tmp_path)
    names = [f"Lobby.B{number}" for number in range(12)]
    takes = "".join(f'  [[screen.take]]\n  image = "{name}"\n' for name in names)
    (folder / "guide.toml").write_text(f'[[screen]]\nname = "Lobby"\n{takes}', encoding="utf-8")
    targets = checks_of(folder)["targets"]
    assert targets.missing == names
    assert targets.found.endswith("and 4 more") and "Lobby.B8" not in targets.found


def test_a_broken_guide_says_to_fix_it(tmp_path):
    folder = bot(tmp_path)
    (folder / "guide.toml").write_text('[[screen]]\nname = "Lobby"\n  [[screen.take]]\n', encoding="utf-8")
    targets = checks_of(folder)["targets"]
    assert targets.ok is False and "guide.toml" in targets.fix


def test_a_broken_darbit_toml_stops_the_checks_and_says_to_fix_it(tmp_path):
    folder = tmp_path / "broken"
    folder.mkdir()
    (folder / "darbit.toml").write_text("[bot]\n", encoding="utf-8")
    checks = doctor.run(folder)
    assert len(checks) == 1 and checks[0].ok is False and "darbit.toml" in checks[0].fix


def test_display_scaling_says_what_to_set_it_back_to(tmp_path, monkeypatch):
    folder = bot(tmp_path)
    (folder / "images" / "Lobby.Play.json").write_text(json.dumps({"scale": 1.0}), encoding="utf-8")
    monkeypatch.setattr(doctor.display, "scale_at", lambda x, y: 1.5)
    scaling = checks_of(folder)["display scaling"]
    assert (
        scaling.ok is False
        and "150%" in scaling.found
        and scaling.fix == "set the display back to 100% for the best matches"
    )
    monkeypatch.setattr(doctor.display, "scale_at", lambda x, y: 1.0)
    scaling = checks_of(folder)["display scaling"]
    assert scaling.ok is True and scaling.fix == "" and "images" in scaling.found


def test_display_scaling_is_a_note_when_it_cant_look(tmp_path, monkeypatch):
    folder = bot(tmp_path)
    assert checks_of(folder)["display scaling"].ok is None  # no image says its scaling

    def unsupported(x, y):
        raise NotSupported("scaling")

    (folder / "images" / "Lobby.Play.json").write_text(json.dumps({"scale": 1.0}), encoding="utf-8")
    monkeypatch.setattr(doctor.display, "scale_at", unsupported)
    scaling = checks_of(folder)["display scaling"]
    assert scaling.ok is None and scaling.fix == ""


def test_a_closed_game_window_says_to_open_it(tmp_path, monkeypatch):
    folder = bot(tmp_path, window="Doc Game")
    monkeypatch.setattr(doctor.windows, "matching", lambda name: [])
    window = checks_of(folder)["game window"]
    assert window.ok is False and window.found == "no window called Doc Game" and window.fix == "open it first"
    monkeypatch.setattr(doctor.windows, "matching", lambda name: ["Doc Game"])
    window = checks_of(folder)["game window"]
    assert window.ok is True and window.fix == ""


def test_a_locked_screen_says_to_unlock_it(tmp_path, monkeypatch):
    folder = bot(tmp_path)
    monkeypatch.setattr(doctor.system, "screen_usable", lambda: False)
    screen = checks_of(folder)["screen"]
    assert screen.ok is False and screen.fix == "unlock it"
    monkeypatch.setattr(doctor.system, "screen_usable", lambda: True)
    screen = checks_of(folder)["screen"]
    assert screen.ok is True and screen.fix == ""


def test_every_problem_has_a_fix_and_every_ok_has_none(tmp_path, monkeypatch):
    folder = bot(tmp_path, window="Doc Game")
    (folder / "images" / "Lobby.Spot.json").write_text(json.dumps({"scale": 1.0}), encoding="utf-8")
    monkeypatch.setattr(doctor.display, "scale_at", lambda x, y: 1.25)
    monkeypatch.setattr(doctor.windows, "matching", lambda name: [])
    monkeypatch.setattr(doctor.system, "screen_usable", lambda: False)
    for check in doctor.run(folder):
        assert bool(check.fix) == (check.ok is False), check.name
