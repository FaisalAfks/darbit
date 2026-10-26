"""Render Storybook stories to PNG images, for reviewing components and for PRs.

    npm run storybook                                   # in another terminal: Storybook on port 6006
    python scripts/render_stories.py                    # every story, every theme, into packages/ui/shots/
    python scripts/render_stories.py --only studio --theme glass-dark

Uses headless Microsoft Edge, like render_mockups.py. The images are not committed (packages/ui/shots/).
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "ui" / "shots"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
THEMES = ["glass-dark", "glass-light", "midnight", "high-contrast"]


def story_ids(server: str) -> list[str]:
    """Every story in the running Storybook."""
    with urllib.request.urlopen(f"{server}/index.json", timeout=10) as response:
        index = json.load(response)
    ids = []
    for entry in index["entries"].values():
        if entry["type"] == "story":
            ids.append(entry["id"])
    return ids


def shoot(server: str, story: str, theme: str, backdrop: str, width: int, height: int) -> Path:
    target = OUT / theme / f"{story}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.mkdtemp(prefix="darbit-story-"))
    url = f"{server}/iframe.html?id={story}&viewMode=story&globals=theme:{theme};backdrop:{backdrop}"
    command = [
        str(EDGE),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        f"--user-data-dir={profile}",
        "--force-device-scale-factor=1",
        f"--window-size={width},{height}",
        "--virtual-time-budget=4000",
        f"--screenshot={target}",
        url,
    ]
    subprocess.run(command, capture_output=True, timeout=90, check=False)  # Edge's exit code isn't reliable
    shutil.rmtree(profile, ignore_errors=True)
    if backdrop == "plain":
        crop_to_content(target)  # a plain background shows where the component ends
    return target


def crop_to_content(path: Path) -> None:
    """Cut the image down to the rows and columns that differ from the corner's background, plus a margin."""
    image = cv2.imread(str(path))
    if image is None:
        return
    background = image[0, 0].astype(np.int16)
    differs = np.abs(image.astype(np.int16) - background).sum(axis=2) > 40
    rows = np.nonzero(differs.any(axis=1))[0]
    columns = np.nonzero(differs.any(axis=0))[0]
    if rows.size == 0 or columns.size == 0:
        return
    margin = 24
    top = max(0, int(rows.min()) - margin)
    bottom = min(image.shape[0], int(rows.max()) + margin)
    left = max(0, int(columns.min()) - margin)
    right = min(image.shape[1], int(columns.max()) + margin)
    cv2.imwrite(str(path), image[top:bottom, left:right])


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Storybook stories to PNG images.")
    parser.add_argument("--server", default="http://127.0.0.1:6006", help="the running Storybook")
    parser.add_argument("--only", default="", help="only stories whose id starts with this")
    parser.add_argument("--theme", choices=THEMES, help="one theme (default: all four)")
    parser.add_argument("--size", default="1280x900", help="window size, e.g. 1280x900")
    parser.add_argument("--backdrop", choices=["plain", "game"], default="plain", help="what the component sits on")
    args = parser.parse_args()
    if not EDGE.is_file():
        print(f"Microsoft Edge not found at {EDGE}")
        return 1
    width, height = (int(part) for part in args.size.split("x"))
    themes = THEMES
    if args.theme:
        themes = [args.theme]
    for story in story_ids(args.server):
        if not story.startswith(args.only):
            continue
        for theme in themes:
            path = shoot(args.server, story, theme, args.backdrop, width, height)
            print(f"{path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
