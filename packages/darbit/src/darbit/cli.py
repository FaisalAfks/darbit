"""The darbit command. See docs/tasks/T19-cli.md.

    darbit new NAME | install GIT_URL | run [PATH] | app | keys
    darbit capture … | guide | highlight | record NAME | play FILE | check | report
"""
from __future__ import annotations

import argparse
import sys

COMMANDS = {
    "new": "make a bot project",
    "install": "install a bot from its git link",
    "run": "run a bot",
    "app": "open the hub",
    "keys": "show the keymap and its conflicts",
    "capture": "capture targets",
    "guide": "open a setup guide",
    "highlight": "show what's found on screen",
    "record": "record a run",
    "play": "play a run file",
    "check": "check the image library",
    "report": "summarise a day's run report",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="darbit")
    parser.add_argument("command", choices=list(COMMANDS), help=", ".join(f"{k}: {v}" for k, v in COMMANDS.items()))
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    raise NotImplementedError(f"TODO(T19): darbit {args.command}")


if __name__ == "__main__":
    sys.exit(main())
