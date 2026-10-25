"""Making, installing and running bot projects: what `darbit new`, `darbit install` and `darbit run` do.

`new` writes a project from the templates next to this file. `install` clones a bot into darbit's bots
folder at its newest release tag and gives it its own environment with uv (decision 0001). `run` starts a
project's entry in that environment. See docs/tasks/T19-cli.md.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from .. import __version__, paths
from .manifest import MANIFEST, find, load

TEMPLATES = Path(__file__).parent / "templates"
NAME_CHARACTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


def good_name(name: str) -> bool:
    """Whether a bot name works as a folder name: letters, digits, - and _."""
    if not name:
        return False
    for character in name:
        if character not in NAME_CHARACTERS:
            return False
    return True


def new(name: str, where: Path) -> Path:
    """A new project folder `where/name` with a manifest, a bot, a setup guide and an images folder."""
    if not good_name(name):
        raise ValueError(f"{name!r}: a bot name is letters, digits, - and _")
    folder = where / name
    if folder.exists() and any(folder.iterdir()):
        raise FileExistsError(f"{folder} already exists and isn't empty")
    (folder / "images").mkdir(parents=True, exist_ok=True)
    (folder / "images" / ".gitkeep").write_text("", encoding="utf-8")
    minor = ".".join(__version__.split(".")[:2])
    for template, target in (
        ("darbit.toml", "darbit.toml"),
        ("bot.py", "bot.py"),
        ("guide.toml", "guide.toml"),
        ("gitignore.txt", ".gitignore"),
    ):
        text = (TEMPLATES / template).read_text(encoding="utf-8")
        text = text.replace("{name}", name).replace("{darbit}", f">={minor}")
        (folder / target).write_text(text, encoding="utf-8", newline="\n")
    return folder


def name_from_url(url: str) -> str:
    """`https://github.com/FaisalAfks/ad-bot.git` -> `ad-bot`."""
    last = url.rstrip("/").replace("\\", "/").rsplit("/", 1)[-1]
    last = last.removesuffix(".git")
    return last


def install(url: str, bots: Path | None = None) -> Path:
    """Clone a bot at its newest release tag and set up its environment. Returns its folder."""
    if bots is None:
        bots = paths.bots_dir()
    name = name_from_url(url)
    if not good_name(name):
        raise ValueError(f"can't make a folder name from {url}")
    folder = bots / name
    if folder.exists():
        raise FileExistsError(f"{name} is already installed in {folder}")
    if shutil.which("git") is None:
        raise RuntimeError("git is needed: winget install Git.Git")
    bots.mkdir(parents=True, exist_ok=True)
    _call(["git", "clone", "--quiet", url, str(folder)])
    tag = newest_tag(folder)
    if tag:
        _call(["git", "-C", str(folder), "checkout", "--quiet", tag])
    make_environment(folder)
    return folder


def newest_tag(folder: Path) -> str:
    """The newest version tag in a clone (v0.10.0 after v0.9.0), or "" when it has none."""
    result = subprocess.run(
        ["git", "-C", str(folder), "tag", "--list", "v*", "--sort=-v:refname"],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.split()
    if not lines:
        return ""
    return lines[0]


def make_environment(folder: Path) -> str:
    """The bot's own environment, with uv: from its pyproject.toml, or its requirements.txt. Says which."""
    has_project = (folder / "pyproject.toml").is_file()
    has_requirements = (folder / "requirements.txt").is_file()
    if not has_project and not has_requirements:
        return "none needed"
    if shutil.which("uv") is None:
        raise RuntimeError("uv is needed: winget install astral-sh.uv")
    if has_project:
        _call(["uv", "sync", "--no-dev"], folder)
        return "pyproject.toml"
    _call(["uv", "venv", "--quiet"], folder)
    _call(["uv", "pip", "install", "--quiet", "-r", "requirements.txt"], folder)
    return "requirements.txt"


def entry_command(entry: str, folder: Path) -> list[str]:
    """The command that starts a project's entry: a script (`bot.py`), a module (`ad_bot`) or a function
    (`ad_bot.main:main`). With the project's own environment when it has a pyproject.toml."""
    if (folder / "pyproject.toml").is_file():
        python = ["uv", "run", "--no-dev", "python"]
    else:
        python = [sys.executable]
    if entry.endswith(".py"):
        return [*python, entry]
    module, _, function = entry.partition(":")
    for part in module.split("."):
        if not part.isidentifier():
            raise ValueError(f"entry {entry!r} isn't a script, a module or module:function")
    if not function:
        return [*python, "-m", module]
    if not function.isidentifier():
        raise ValueError(f"entry {entry!r} isn't a script, a module or module:function")
    return [*python, "-c", f"from {module} import {function}; {function}()"]


def run(start: Path) -> int:
    """Run the project at or above `start`. Returns the bot's exit code."""
    folder = find(start)
    if folder is None:
        raise FileNotFoundError(f"no {MANIFEST} in {start} or above it")
    project = load(folder)
    process = subprocess.Popen(entry_command(project.entry, folder), cwd=folder)
    try:
        return process.wait()
    except KeyboardInterrupt:
        # Ctrl+C reached the bot too (same console); let it finish its own way
        return process.wait()


def _call(command: list[str], folder: Path | None = None) -> None:
    subprocess.run(command, cwd=folder, check=True)
