"""A day's run report, summarised.

    python -m darbit.tools.report                 # today, from logs/ next to the current folder
    python -m darbit.tools.report 2026-10-21 --logs ../ad-bot/logs

Shows each step (how often it ran, how often it failed, its average and longest time),
the reasons steps failed with their screenshots, the targets most often not found with
the closest score they got, and the bot's own events (d.record) counted by name.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SEARCHES = ("exists", "wait")


def read(path: Path) -> list[dict]:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a line cut short by a crash
    return events


def summary(events: list[dict]) -> str:
    out: list[str] = []

    steps: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        if e.get("event") == "step" and e.get("state") != "started":
            steps[e["step"]].append(e)
    if steps:
        width = max(len(s) for s in steps)
        out.append(f"{'step':<{width}}  runs  ok  failed  interrupted  avg s  max s")
        for name, ends in sorted(steps.items()):
            times = [e.get("seconds", 0) for e in ends]
            states = Counter(e["state"] for e in ends)
            out.append(
                f"{name:<{width}}  {len(ends):4}  {states['ok']:2}  {states['failed']:6}  "
                f"{states['interrupted']:11}  {sum(times) / len(times):5.1f}  {max(times):5.1f}"
            )

    failures = [e for e in events if e.get("event") == "step" and e.get("state") in ("failed", "interrupted")]
    if failures:
        out.append("")
        out.append("why steps ended early:")
        for (where, reason), n in Counter((e["step"], e.get("reason", "")) for e in failures).most_common(10):
            shot = next(
                (
                    e.get("screenshot")
                    for e in reversed(failures)
                    if e["step"] == where and e.get("reason", "") == reason and e.get("screenshot")
                ),
                None,
            )
            out.append(f"  {n:3}x  {where}: {reason}" + (f"  ({shot})" if shot else ""))

    misses = [e for e in events if e.get("event") in SEARCHES and e.get("found") is None and e.get("timeout", 0) > 0]
    if misses:
        out.append("")
        out.append("most often not found (closest score):")
        counted = Counter(e["targets"] for e in misses)
        for target, n in counted.most_common(10):
            scores = [e["closest"] for e in misses if e["targets"] == target and e.get("closest") is not None]
            out.append(f"  {n:4}x  {target}" + (f"  (closest {max(scores):.2f})" if scores else ""))

    own = Counter(
        e["event"]
        for e in events
        if e.get("event") not in (*SEARCHES, "step", "click", "double_click", "right_click", "drag")
    )
    if own:
        out.append("")
        out.append("events:")
        for name, n in own.most_common():
            out.append(f"  {n:4}x  {name}")

    return "\n".join(out) if out else "nothing recorded"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m darbit.tools.report", description="Summarise a day's run report.")
    parser.add_argument("day", nargs="?", default=datetime.now().strftime("%Y-%m-%d"), help="YYYY-MM-DD (today)")
    parser.add_argument("--logs", default=".darbit/logs", help="the logs folder (default: .darbit/logs)")
    args = parser.parse_args(argv)
    path = Path(args.logs) / f"report-{args.day}.jsonl"
    if not path.is_file():
        print(f"no report for {args.day} in {args.logs}")
        return 1
    print(summary(read(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
