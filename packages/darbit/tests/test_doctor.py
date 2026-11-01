"""darbit doctor: a bot's readiness, checked from its files and this system."""

import json

from darbit import cli, doctor


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


def test_missing_pictures_are_named_and_fail_the_check(tmp_path, capsys):
    folder = bot(tmp_path)
    (folder / "images" / "Lobby.Spot.json").write_text(json.dumps({"location": [1, 2]}), encoding="utf-8")
    checks = {check.name: check for check in doctor.run(folder)}
    assert checks["darbit.toml"].ok is True
    assert checks["pictures"].ok is False and "Lobby.Play" in checks["pictures"].say
    assert "Lobby.Spot" not in checks["pictures"].say  # a point has no picture
    assert checks["game window"].ok is None  # none named
    assert cli.main(["doctor", str(folder)]) == 1
    assert "!!  pictures" in capsys.readouterr().out


def test_a_broken_darbit_toml_stops_the_checks(tmp_path):
    folder = tmp_path / "broken"
    folder.mkdir()
    (folder / "darbit.toml").write_text("[bot]\n", encoding="utf-8")
    checks = doctor.run(folder)
    assert len(checks) == 1 and checks[0].ok is False
