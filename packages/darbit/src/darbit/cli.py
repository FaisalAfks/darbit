"""The darbit command. See docs/tasks/T19-cli.md.

darbit new NAME | install GIT_URL | run [PATH]
darbit capture … | guide [FILE] | check … | report …     the tools, same options as python -m darbit.<tool>
darbit app | keys | highlight | record | play             come with their tasks

Each command hands its arguments to the module that does the work: project/bots.py for new, install and
run, and each tool's own main().
"""

import argparse
import subprocess
import sys
from pathlib import Path

COMMANDS = {
    "new": "make a bot project",
    "install": "install a bot from its git link",
    "run": "run a bot",
    "capture": "capture targets",
    "guide": "walk through a bot's setup guide",
    "check": "check the image library",
    "report": "summarise a day's run report",
    "app": "open darbit Studio",
    "keys": "show the keymap and its conflicts",
    "highlight": "show what's found on screen",
    "record": "record a run",
    "play": "play a run file",
}

# commands whose task isn't done yet
LATER = {"app": "T20", "keys": "T04", "highlight": "T11", "record": "T15", "play": "T16"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="darbit", description="Simple GUI automation for Windows.")
    lines = []
    for name, text in COMMANDS.items():
        lines.append(f"{name}: {text}")
    parser.add_argument("command", choices=list(COMMANDS), help="; ".join(lines))
    parser.add_argument("rest", nargs=argparse.REMAINDER, help="the command's own arguments (darbit COMMAND -h)")
    args = parser.parse_args(argv)
    command = args.command

    if command in LATER:
        print(f"darbit {command} isn't built yet ({LATER[command]} in docs/tasks)")
        return 2
    if command == "new":
        return _new(args.rest)
    if command == "install":
        return _install(args.rest)
    if command == "run":
        return _run(args.rest)
    return _tool(command, args.rest)


def _new(argv: list[str]) -> int:
    from .project import bots

    parser = argparse.ArgumentParser(prog="darbit new", description="Make a bot project folder.")
    parser.add_argument("name", help="the bot's name, also its folder: letters, digits, - and _")
    parser.add_argument("--where", default=".", help="the folder to make it in (default: here)")
    args = parser.parse_args(argv)
    try:
        folder = bots.new(args.name, Path(args.where))
    except (ValueError, FileExistsError) as error:
        print(error)
        return 2
    print(f"made {folder}")
    print(f"next: cd {folder}, take its pictures with darbit guide, then darbit run")
    return 0


def _install(argv: list[str]) -> int:
    from .project import bots

    parser = argparse.ArgumentParser(prog="darbit install", description="Install a bot from its git link.")
    parser.add_argument("url", help="the bot's git link, e.g. https://github.com/me/my-bot")
    parser.add_argument("--into", help="the bots folder (default: darbit's, in %%LOCALAPPDATA%%\\darbit\\bots)")
    args = parser.parse_args(argv)
    into = None
    if args.into:
        into = Path(args.into)
    try:
        folder = bots.install(args.url, into)
    except (ValueError, FileExistsError, RuntimeError) as error:
        print(error)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"{' '.join(error.cmd)} failed (exit code {error.returncode})")
        return 1
    print(f"installed in {folder}")
    if (folder / "guide.toml").is_file():
        print(f"next: take its pictures with darbit guide {folder / 'guide.toml'}")
    print(f"run it with: darbit run {folder}")
    return 0


def _run(argv: list[str]) -> int:
    from .project import bots

    parser = argparse.ArgumentParser(prog="darbit run", description="Run a bot project.")
    parser.add_argument("path", nargs="?", default=".", help="the project folder, or a folder inside it")
    args = parser.parse_args(argv)
    try:
        return bots.run(Path(args.path))
    except (FileNotFoundError, ValueError) as error:
        print(error)
        return 2


def _tool(command: str, argv: list[str]) -> int:
    if command == "capture":
        from .capture import main as capture

        return capture(argv)
    if command == "guide":
        from .capture import main as capture

        if not argv or argv[0].startswith("-"):
            argv = ["guide.toml", *argv]
        return capture(["--guide", *argv])
    if command == "check":
        from .tools.check import main as check

        return check(argv)
    from .tools.report import main as report

    return report(argv)


if __name__ == "__main__":
    sys.exit(main())
