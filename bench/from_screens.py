"""Turn the screens a bot's Studio saved into bench cases: each screen with every asset boxed on it.

    uv run python bench/from_screens.py ../ad-bot ../darbit-bench/ad-bot      # one case per saved screen

darbit Studio's Capture keeps the last shot of each screen in the bot's `.darbit/screens/` (`<screen>.jpg` and
`<screen>.json` with each asset's box). A case gets that shot, the images it names from the bot's images folder,
and `at` for each. Saved shots are JPEG, so scores come out a little lower than on a live screen.
"""

import argparse
import json
import shutil
import sys
import tomllib
from pathlib import Path


def images_folder(bot: Path) -> Path:
    manifest = tomllib.loads((bot / "darbit.toml").read_text(encoding="utf-8"))
    folders = manifest.get("images", {}).get("folders", ["images"])
    return bot / folders[0]


def scale_of(images: Path, names: list[str]) -> float:
    """The display scaling the bot's images were taken at (their .json's `scale`), 1.0 if none says."""
    for name in names:
        settings = images / f"{name}.json"
        if settings.is_file():
            value = json.loads(settings.read_text(encoding="utf-8")).get("scale")
            if value:
                return float(value)
    return 1.0


def convert(bot: Path, into: Path) -> int:
    screens = bot / ".darbit" / "screens"
    images = images_folder(bot)
    made = 0
    for places_file in sorted(screens.glob("*.json")):
        places = json.loads(places_file.read_text(encoding="utf-8"))
        shot = places_file.with_suffix(".jpg")
        assets = places.get("assets", {})
        kept = []
        for name, place in assets.items():
            if place.get("kind") == "image" and (images / f"{name}.png").is_file():
                kept.append(name)
        if not shot.is_file() or not kept:
            continue
        case = into / places_file.stem
        (case / "images").mkdir(parents=True, exist_ok=True)
        shutil.copy(shot, case / "screen.jpg")
        lines = [f"# {bot.name}'s {places_file.stem} screen, saved by darbit Studio (JPEG)", 'screen = "screen.jpg"']
        lines += ['images = "images"', f"scale = {scale_of(images, kept)}", ""]
        for name in kept:
            for suffix in (".png", ".json"):
                source = images / f"{name}{suffix}"
                if source.is_file():
                    shutil.copy(source, case / "images" / source.name)
            lines += ["[[find]]", f'target = "{name}"', f"at = {assets[name]['box']}", ""]
        (case / "case.toml").write_text("\n".join(lines), encoding="utf-8", newline="\n")
        made += 1
    return made


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bench cases from a bot's saved screens.")
    parser.add_argument("bot", type=Path, help="the bot's folder")
    parser.add_argument("into", type=Path, help="where the cases go")
    args = parser.parse_args(argv)
    made = convert(args.bot, args.into)
    print(f"{made} case(s) in {args.into}")
    return 0 if made else 1


if __name__ == "__main__":
    sys.exit(main())
