"""The darbit command.

darbit new NAME | install GIT_URL | run [PATH]
darbit check … | report …     the tools, same options as python -m darbit.tools.<tool>
darbit serve                  darbit's service: runs bots whether the Studio is open or not
darbit bots | status BOT | start BOT | pause BOT | stop BOT | history BOT [DAY] | notify
                              bots through the service (started in the background if it isn't running)
darbit app                    darbit Studio is being rebuilt (docs/plan-rebuild.md): says where v0.4's is

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
    "check": "check the image library",
    "report": "summarise a day's run report",
    "serve": "run darbit's service",
    "bots": "list the bots the service knows",
    "status": "show a bot: running, paused or stopped",
    "start": "start a bot through the service",
    "pause": "pause a running bot, or go on",
    "stop": "stop a bot",
    "history": "show what a bot did on a day",
    "notify": "send a test notification to the channels in notify.toml",
    "app": "open darbit Studio",
}
BOT_COMMANDS = {"status": "bot.status", "start": "bot.start", "pause": "bot.pause", "stop": "bot.stop"}

STUDIO_MOVED = (
    "darbit Studio is being rebuilt (docs/plan-rebuild.md). Until it's back, run v0.4's from a checkout of the "
    "v0.4.0 tag: git clone --branch v0.4.0 https://github.com/FaisalAfks/darbit, then uv run --all-extras darbit app"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="darbit", description="Automate any app from what's on its screen.")
    lines = []
    for name, text in COMMANDS.items():
        lines.append(f"{name}: {text}")
    parser.add_argument("command", choices=list(COMMANDS), help="; ".join(lines))
    parser.add_argument("rest", nargs=argparse.REMAINDER, help="the command's own arguments (darbit COMMAND -h)")
    args = parser.parse_args(argv)
    command = args.command

    if command == "app":
        print(STUDIO_MOVED)
        return 2
    if command == "new":
        return _new(args.rest)
    if command == "install":
        return _install(args.rest)
    if command == "run":
        return _run(args.rest)
    if command == "serve":
        return _serve(args.rest)
    if command == "bots":
        return _bots(args.rest)
    if command == "history":
        return _history(args.rest)
    if command == "notify":
        return _notify(args.rest)
    if command in BOT_COMMANDS:
        return _bot(command, args.rest)
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
    print(f"next: cd {folder}, take its pictures, then darbit run")
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


def _serve(argv: list[str]) -> int:
    from .service import client
    from .service.host import Service

    parser = argparse.ArgumentParser(prog="darbit serve", description="Run darbit's service until it's stopped.")
    parser.add_argument("--port", type=int, default=0, help="the port on 127.0.0.1 (default: any free one)")
    parser.add_argument("--stop", action="store_true", help="stop the running service (its bots go on)")
    args = parser.parse_args(argv)
    if args.stop:
        try:
            with client.Client("darbit cli") as service:
                service.call("service.stop")
        except client.ServiceError as error:
            print(error)
            return 1
        print("darbit's service is stopping")
        return 0
    if client.running():
        print("darbit's service is already running")
        return 0
    service = Service(args.port)
    print(f"darbit's service on 127.0.0.1:{service.port}; Ctrl+C stops it (running bots go on)")
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def _bots(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="darbit bots", description="List the bots the service knows.")
    parser.add_argument("--add", metavar="PATH", help="add a project folder (one with a darbit.toml) first")
    args = parser.parse_args(argv)
    if args.add and _ask("bots.add", path=str(Path(args.add).resolve())) is None:
        return 1
    found = _ask("bots.list")
    if found is None:
        return 1
    if not found:
        print("no bots yet: darbit install GIT_URL, or darbit new NAME")
    for bot in found:
        print(f"{bot.get('name', '?'):24} {bot.get('status', ''):8} {bot.get('path', '')}")
    return 0


def _bot(command: str, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog=f"darbit {command}", description=COMMANDS[command] + ".")
    parser.add_argument("bot", help="the bot's name, or its folder")
    args = parser.parse_args(argv)
    result = _ask(BOT_COMMANDS[command], bot=args.bot)
    if result is None:
        return 1
    print(f"{args.bot}: {result.get('status', result)}")
    return 0


def _history(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="darbit history", description="Show what a bot did on a day.")
    parser.add_argument("bot", help="the bot's name, or its folder")
    parser.add_argument("day", nargs="?", help="the day, e.g. 2026-10-31 (default: the latest)")
    parser.add_argument("--days", action="store_true", help="list the days instead")
    args = parser.parse_args(argv)
    from .server.results import clock

    days = _ask("bot.days", bot=args.bot)
    if days is None:
        return 1
    if not days:
        print(f"{args.bot} has no history yet")
        return 0
    if args.days:
        for row in days:
            lead = row.get("lead") or {}
            gain = f"{lead.get('amount')} {lead.get('name')}" if lead else ""
            print(f"{row['day']}  {clock(row.get('seconds', 0)):>8}  problems {row.get('problems', 0):<4} {gain}")
        return 0
    found = _ask("bot.day", bot=args.bot, day=args.day or days[0]["day"])
    if found is None:
        return 1
    from .server.results import day_lines

    for line in day_lines(found):
        print(line)
    return 0


def _notify(argv: list[str]) -> int:
    from .service import notify

    parser = argparse.ArgumentParser(prog="darbit notify", description=COMMANDS["notify"] + ".")
    parser.add_argument("text", nargs="?", default="darbit can reach you here", help="what to send")
    args = parser.parse_args(argv)
    settings = notify.load_settings()
    if not settings.channels:
        print(f"no channels set: add [ntfy], [discord] or [telegram] to {notify.settings_file()}")
        return 2
    failed = 0
    for channel in settings.channels:
        if notify.post(channel, "darbit", args.text):
            print(f"sent to {channel.name}")
        else:
            print(f"couldn't reach {channel.name}: check its settings in {notify.settings_file()}")
            failed += 1
    return 1 if failed else 0


def _ask(method: str, **params: object) -> object:
    """The service's answer, starting the service first if needed; None after printing why it failed."""
    from .service import client

    try:
        client.ensure_running()
        with client.Client("darbit cli") as service:
            return service.call(method, **params)
    except client.ServiceError as error:
        print(error)
        return None


def _tool(command: str, argv: list[str]) -> int:
    if command == "check":
        from .tools.check import main as check

        return check(argv)
    from .tools.report import main as report

    return report(argv)


if __name__ == "__main__":
    sys.exit(main())
