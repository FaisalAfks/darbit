"""Render docs/ui/mockups.html to PNG images, one per section, theme and state.

    python scripts/render_mockups.py                 # all shots into docs/ui/images/
    python scripts/render_mockups.py --only studio   # only shots whose name starts with "studio"

Uses headless Microsoft Edge (installed with Windows). Animations are off in the page's
screenshot mode, so nothing renders half-faded. Blank space under a section is cropped.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "ui" / "mockups.html"
OUT = ROOT / "docs" / "ui" / "images"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
PHONE = 390  # headless Edge never goes below 504 px wide, so phone shots render inside a frame this wide

# name: (query string, window width, window height)
SHOTS = {
    "capture-dark": ("shot=capture&theme=glass-dark", 1200, 820),
    "capture-light": ("shot=capture&theme=glass-light", 1200, 820),
    "capture-midnight": ("shot=capture&theme=midnight", 1200, 820),
    "capture-contrast": ("shot=capture&theme=high-contrast", 1200, 820),
    "highlight-dark": ("shot=highlight&theme=glass-dark", 1200, 820),
    "recorder-paused-dark": ("shot=recorder&theme=glass-dark&paused=1", 1200, 640),
    "studio-bots-dark": ("shot=studio&theme=glass-dark&view=bots", 1200, 760),
    "studio-bots-light": ("shot=studio&theme=glass-light&view=bots", 1200, 760),
    "studio-empty-dark": ("shot=studio&theme=glass-dark&state=empty", 1200, 760),
    "studio-tools-dark": ("shot=studio&theme=glass-dark&view=tools", 1200, 760),
    "studio-flows-dark": ("shot=studio&theme=glass-dark&view=flows", 1200, 760),
    "studio-wizard-dark": ("shot=studio&theme=glass-dark&wizard=2", 1200, 760),
    "studio-install-error-dark": ("shot=studio&theme=glass-dark&state=error", 1200, 760),
    "flow-python-dark": ("shot=flow&theme=glass-dark", 1200, 560),
    "tokens-keys-contrast": ("shot=tokens&theme=high-contrast", 1200, 560),
    "capture-phone-dark": ("shot=capture&theme=glass-dark", PHONE, 900),
    "studio-phone-dark": ("shot=studio&theme=glass-dark&view=flows", PHONE, 900),
}


def shoot(name: str, query: str, width: int, height: int) -> Path:
    """Take one screenshot with a fresh Edge profile, so runs never share state."""
    target = OUT / f"{name}.png"
    profile = Path(tempfile.mkdtemp(prefix="darbit-shot-"))
    url = PAGE.as_uri() + "?" + query
    narrow = width < 504
    if narrow:
        frame = profile / "frame.html"
        frame.write_text(
            f'<body style="margin:0;background:#000"><iframe src="{url}" '
            f'style="border:0;width:{width}px;height:{height}px"></iframe>',
            encoding="utf-8",
        )
        url, width = frame.as_uri(), 600
    command = [
        str(EDGE),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        f"--user-data-dir={profile}",
        "--force-device-scale-factor=1",
        f"--window-size={width},{height}",
        "--virtual-time-budget=2500",
        f"--screenshot={target}",
        url,
    ]
    subprocess.run(
        command, capture_output=True, timeout=60, check=False
    )  # Edge's exit code isn't reliable; the file is checked
    shutil.rmtree(profile, ignore_errors=True)
    if narrow:
        image = cv2.imread(str(target))
        cv2.imwrite(str(target), image[:, :PHONE])
    crop_blank_bottom(target)
    return target


def crop_blank_bottom(path: Path) -> None:
    """Cut off the empty page background below the last row with anything on it."""
    image = cv2.imread(str(path))
    if image is None:
        return
    busy_rows = np.nonzero(image.std(axis=(1, 2)) > 2)[0]
    if busy_rows.size:
        bottom = min(image.shape[0], int(busy_rows.max()) + 24)
        cv2.imwrite(str(path), image[:bottom])


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the UI mockups to PNG images.")
    parser.add_argument("--only", default="", help="only shots whose name starts with this")
    args = parser.parse_args()
    if not EDGE.is_file():
        print(f"Microsoft Edge not found at {EDGE}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (query, width, height) in SHOTS.items():
        if name.startswith(args.only):
            path = shoot(name, query, width, height)
            print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
