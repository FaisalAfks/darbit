"""Make the bench's made-up cases: screens drawn from code, with every target's true place known.

    uv run python bench/make_cases.py      # writes bench/cases/<case>/ (screen.png, images/, case.toml)

bench/run.py makes them when they're missing, so they aren't committed (the noisy screens are a few MB).

The screens look like a game's menus: panels, buttons with labels, icons, a noisy backdrop. Each case also has
targets that must not be found (a look-alike, something not on screen) and, in `scaled-1920`, the same screen
at another size, which plain matching isn't expected to find (it measures resizing options later).
"""

import json
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).parent / "cases"
SEED = 7


def backdrop(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
    """A dark gradient with soft noise, like a game scene behind its menus."""
    ys = np.linspace(0, 1, height, dtype=np.float32)[:, None]
    xs = np.linspace(0, 1, width, dtype=np.float32)[None, :]
    blue = 40 + 50 * ys + 20 * xs
    green = 20 + 30 * xs
    red = 30 + 40 * (1 - ys)
    image = np.dstack([blue + 0 * xs, green + 0 * ys, red + 0 * xs])
    image += rng.normal(0, 6, image.shape).astype(np.float32)
    return np.clip(image, 0, 255).astype(np.uint8)


def button(image: np.ndarray, x: int, y: int, w: int, h: int, text: str, colour: tuple[int, int, int]) -> list[int]:
    """A rounded button with a label; returns its box."""
    cv2.rectangle(image, (x, y), (x + w, y + h), colour, -1, cv2.LINE_AA)
    cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), 2, cv2.LINE_AA)
    size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 1.1, 2)
    origin = (x + (w - size[0]) // 2, y + (h + size[1]) // 2)
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_DUPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)
    return [x, y, w, h]


def icon(image: np.ndarray, x: int, y: int, size: int, seed: int) -> list[int]:
    """A small coloured icon: a gradient tile with a shape on it; returns its box."""
    rng = np.random.default_rng(seed)
    tile = np.zeros((size, size, 3), np.uint8)
    start = rng.integers(40, 200, 3)
    end = rng.integers(40, 200, 3)
    for row in range(size):
        share = row / size
        tile[row, :] = (start * (1 - share) + end * share).astype(np.uint8)
    centre = (size // 2, size // 2)
    cv2.circle(tile, centre, size // 3, tuple(int(v) for v in rng.integers(150, 255, 3)), -1, cv2.LINE_AA)
    cv2.rectangle(tile, (size // 4, size // 4), (size // 2, size // 2), (20, 20, 20), -1)
    image[y : y + size, x : x + size] = tile
    return [x, y, size, size]


def panel(image: np.ndarray, x: int, y: int, w: int, h: int) -> list[int]:
    overlay = image.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (30, 26, 22), -1)
    cv2.addWeighted(overlay, 0.85, image, 0.15, 0, image)
    cv2.rectangle(image, (x, y), (x + w, y + h), (90, 90, 90), 2)
    return [x, y, w, h]


def menu_screen() -> tuple[np.ndarray, dict[str, list[int]]]:
    """The main made-up screen at 2560 x 1600, and the true box of everything on it."""
    rng = np.random.default_rng(SEED)
    image = backdrop(2560, 1600, rng)
    boxes: dict[str, list[int]] = {}
    boxes["Menu.Panel"] = panel(image, 440, 280, 1660, 1080)
    boxes["Menu.Play"] = button(image, 2140, 1340, 340, 150, "PLAY", (60, 140, 230))
    boxes["Menu.Shop"] = button(image, 2140, 1160, 340, 120, "SHOP", (80, 180, 90))
    boxes["Menu.Bag"] = button(image, 2140, 1000, 340, 120, "BAG", (170, 110, 60))
    boxes["Menu.Claim"] = button(image, 1000, 1200, 300, 100, "CLAIM", (40, 60, 210))
    boxes["Menu.Close"] = button(image, 2020, 300, 60, 60, "X", (40, 40, 200))
    for index in range(10):
        column = index % 5
        row = index // 5
        boxes[f"Char.{index}"] = icon(image, 520 + column * 300, 400 + row * 330, 180, SEED + index)
    # a look-alike of Claim: the same button with one letter different
    boxes["Menu.Clamp"] = button(image, 1400, 1200, 300, 100, "CLAMP", (40, 60, 210))
    return image, boxes


def crop(image: np.ndarray, box: list[int]) -> np.ndarray:
    x, y, w, h = box
    return image[y : y + h, x : x + w].copy()


def write_case(
    name: str,
    screen: np.ndarray,
    targets: dict[str, np.ndarray],
    settings: dict[str, dict],
    finds: list[dict],
    note: str,
) -> None:
    folder = HERE / name
    images = folder / "images"
    images.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(folder / "screen.png"), screen)
    for target_name, pixels in targets.items():
        cv2.imwrite(str(images / f"{target_name}.png"), pixels)
        extra = settings.get(target_name)
        if extra:
            (images / f"{target_name}.json").write_text(json.dumps(extra, indent=2) + "\n", encoding="utf-8")
    lines = [f"# {note}", 'screen = "screen.png"', 'images = "images"', ""]
    for find in finds:
        lines.append("[[find]]")
        lines.append(f'target = "{find["target"]}"')
        if "at" in find:
            lines.append(f"at = {find['at']}")
        else:
            lines.append("absent = true")
        if "option" in find:
            lines.append(f'option = "{find["option"]}"')
        lines.append("")
    (folder / "case.toml").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    screen, boxes = menu_screen()
    names = ["Menu.Play", "Menu.Shop", "Menu.Bag", "Menu.Claim", "Menu.Close", "Char.0", "Char.3", "Char.7", "Char.9"]
    targets = {name: crop(screen, boxes[name]) for name in names}
    # a picture that isn't on screen: a striped tile, unlike every icon
    missing = np.zeros((180, 180, 3), np.uint8)
    for stripe in range(0, 180, 20):
        cv2.rectangle(missing, (stripe, 0), (stripe + 9, 179), (220, 220, 40), -1)
    targets["Char.Missing"] = missing
    # Char.0 in other colours: plain template matching mostly ignores colour, so only a colour option tells them apart
    twin = cv2.cvtColor(targets["Char.0"], cv2.COLOR_BGR2HSV)
    twin[:, :, 0] = (twin[:, :, 0].astype(np.int16) + 60) % 180
    targets["Char.ColourTwin"] = cv2.cvtColor(twin, cv2.COLOR_HSV2BGR)
    settings = {
        "Menu.Claim": {"similarity": 0.9},  # strict, so the CLAMP look-alike doesn't count
        "Char.3": {"region": [440, 280, 1660, 1080]},  # searched only inside the panel
        "Char.7": {"region": [440, 280, 1660, 1080]},
        "Menu.Close": {"region": [1900, 260, 300, 200]},
    }
    finds = [{"target": name, "at": boxes[name]} for name in names]
    finds.append({"target": "Char.Missing"})
    finds.append({"target": "Char.ColourTwin", "option": "colour"})
    write_case("menu-2560", screen, targets, settings, finds, "made-up menus at 2560 x 1600; every target taken here")

    scaled = cv2.resize(screen, (1920, 1200), interpolation=cv2.INTER_AREA)
    scaled_finds = []
    for name in ["Menu.Play", "Menu.Shop", "Char.0"]:
        x, y, w, h = boxes[name]
        scaled_finds.append({"target": name, "at": [round(v * 0.75) for v in (x, y, w, h)], "option": "sizes"})
    write_case(
        "scaled-1920",
        scaled,
        {name: targets[name] for name in ["Menu.Play", "Menu.Shop", "Char.0"]},
        {},
        scaled_finds,
        "the same menus at 1920 x 1200 with targets taken at 2560: found only with a resizing option",
    )
    print(f"cases written to {HERE}")


if __name__ == "__main__":
    main()
