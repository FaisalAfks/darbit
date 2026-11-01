"""The darbit command: new, install (from a local repo, no network), run, and handing over to the tools."""

import subprocess
import sys
import tomllib

import pytest

import darbit
from darbit import cli
from darbit.project import bots
from darbit.project.manifest import load


def git(*args, cwd=None):
    command = ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args]
    subprocess.run(command, cwd=cwd, check=True, capture_output=True)


def test_new_makes_a_project(tmp_path):
    assert cli.main(["new", "my-bot", "--where", str(tmp_path)]) == 0
    folder = tmp_path / "my-bot"
    for name in (
        "pyproject.toml",
        "darbit.toml",
        "guide.toml",
        ".gitignore",
        "assets/images/.gitkeep",
        "src/my_bot/__init__.py",
        "src/my_bot/bot.py",
    ):
        assert (folder / name).is_file(), name
    project = load(folder)
    assert project.name == "my-bot"
    assert project.entry == "my_bot.bot:main"
    assert project.images == ["assets/images"]
    assert project.darbit == ">=" + ".".join(darbit.__version__.split(".")[:2])
    pyproject = tomllib.loads((folder / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["scripts"] == {"my-bot": "my_bot.bot:main"}
    source = pyproject["tool"]["uv"]["sources"]["darbit"]
    if ".dev" in darbit.__version__:
        assert source["branch"] == "main"  # a development darbit has no release tag to pin to
    else:
        assert source["tag"] == "v" + darbit.__version__
    tomllib.loads((folder / "guide.toml").read_text(encoding="utf-8"))
    compile((folder / "src/my_bot/bot.py").read_text(encoding="utf-8"), "bot.py", "exec")


def test_new_refuses_a_bad_name_or_a_full_folder(tmp_path, capsys):
    assert cli.main(["new", "my bot!", "--where", str(tmp_path)]) == 2
    assert cli.main(["new", "1bot", "--where", str(tmp_path)]) == 2  # not a Python package name
    assert cli.main(["new", "my-bot", "--where", str(tmp_path)]) == 0
    assert cli.main(["new", "my-bot", "--where", str(tmp_path)]) == 2
    assert "isn't empty" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("url", "name"),
    [
        ("https://github.com/FaisalAfks/ad-bot", "ad-bot"),
        ("https://github.com/FaisalAfks/ad-bot.git", "ad-bot"),
        ("https://github.com/me/hello_bot/", "hello_bot"),
        ("C:\\bots\\local-bot", "local-bot"),
    ],
)
def test_name_from_url(url, name):
    assert bots.name_from_url(url) == name


def make_repo(tmp_path):
    """A bot repo with two releases and a newer commit after them."""
    repo = bots.new("test-bot", tmp_path / "source")
    (repo / "pyproject.toml").unlink()  # no environment to make: no network in tests
    git("init", "--quiet", cwd=repo)
    git("add", ".", cwd=repo)
    git("commit", "--quiet", "-m", "first", cwd=repo)
    git("tag", "v0.9.0", cwd=repo)
    (repo / "src/test_bot/bot.py").write_text("print('v0.10')\n", encoding="utf-8")
    git("commit", "--quiet", "-am", "second", cwd=repo)
    git("tag", "v0.10.0", cwd=repo)
    (repo / "src/test_bot/bot.py").write_text("print('not released')\n", encoding="utf-8")
    git("commit", "--quiet", "-am", "third", cwd=repo)
    return repo


def test_install_clones_at_the_newest_release(tmp_path):
    repo = make_repo(tmp_path)
    folder = bots.install(str(repo), tmp_path / "bots")
    assert folder == tmp_path / "bots" / "test-bot"
    assert (folder / "src/test_bot/bot.py").read_text(encoding="utf-8") == "print('v0.10')\n"
    assert bots.newest_tag(folder) == "v0.10.0"
    with pytest.raises(FileExistsError):
        bots.install(str(repo), tmp_path / "bots")


def test_install_from_the_command(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert cli.main(["install", str(repo), "--into", str(tmp_path / "bots")]) == 0
    out = capsys.readouterr().out
    assert "installed in" in out


def test_entry_commands(tmp_path):
    python = sys.executable
    assert bots.entry_command("bot.py", tmp_path) == [python, "bot.py"]
    assert bots.entry_command("ad_bot", tmp_path) == [python, "-m", "ad_bot"]
    assert bots.entry_command("ad_bot.main:main", tmp_path) == [python, "-c", "from ad_bot.main import main; main()"]
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    assert bots.entry_command("bot.py", tmp_path)[:3] == ["uv", "run", "--no-dev"]
    with pytest.raises(ValueError):
        bots.entry_command("ad_bot; rm -rf", tmp_path)
    with pytest.raises(ValueError):
        bots.entry_command("ad_bot:main()", tmp_path)


def test_run_starts_the_entry_in_the_project(tmp_path):
    folder = bots.new("runner", tmp_path)
    (folder / "pyproject.toml").unlink()  # run with this Python, not uv
    (folder / "darbit.toml").write_text('[bot]\nname = "runner"\nentry = "bot.py"\n', encoding="utf-8")
    (folder / "bot.py").write_text("import sys\nopen('ran.txt', 'w').write('yes')\nsys.exit(3)\n", encoding="utf-8")
    assert cli.main(["run", str(folder / "src" / "runner")]) == 3  # found from a folder inside the project
    assert (folder / "ran.txt").read_text(encoding="utf-8") == "yes"


def test_run_without_a_project(tmp_path, capsys):
    assert cli.main(["run", str(tmp_path)]) == 2
    assert "no darbit.toml" in capsys.readouterr().out


def test_the_studio_command_opens_the_studio_or_says_what_it_needs(capsys, monkeypatch):
    import sys
    import types

    opened = []
    studio = types.ModuleType("darbit.studio.app")
    studio.main = lambda argv: opened.append(argv) or 0
    monkeypatch.setitem(sys.modules, "darbit.studio.app", studio)
    assert cli.main(["app"]) == 0
    assert len(opened) == 1
    monkeypatch.setitem(sys.modules, "darbit.studio.app", None)  # PySide6 not installed
    assert cli.main(["app"]) == 2
    assert "darbit[studio]" in capsys.readouterr().out


def test_an_unknown_command_is_refused():
    with pytest.raises(SystemExit):
        cli.main(["fly"])


def test_app_shortcut_opens_the_studio_without_a_console_and_with_darbits_icon(monkeypatch, capsys):
    from darbit.platform import system

    made = []

    def add_shortcut(name, target, arguments, icon):
        made.append((name, target, arguments, icon))
        return [icon.parent / f"{name}.lnk"]

    monkeypatch.setattr(system, "add_shortcut", add_shortcut)
    assert cli.main(["app", "--shortcut"]) == 0
    name, target, arguments, icon = made[0]
    assert name == "darbit Studio"
    assert arguments == "-m darbit app"
    assert icon.name == "darbit.ico" and icon.is_file()
    if target.with_name("pythonw.exe").is_file():
        assert target.name == "pythonw.exe"
    assert "made" in capsys.readouterr().out
