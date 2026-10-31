"""darbit Studio's themes: the design system's tokens (docs/style/ui/design-system.md), as QML colours.

The values are the ones in docs/ui/mockups.html, written the CSS way (`rgb(22 25 33 / .74)`, `#5ac8fa`) and turned
into Qt's `#AARRGGBB`. A custom theme (theme.toml in darbit's settings folder) overrides any of them on top of a
base theme, as before: `base = "glass-dark"`, `accent = "#ff7ab6"`.
"""

import re
import tomllib
from pathlib import Path

DEFAULT = "glass-dark"

THEMES: dict[str, dict[str, str]] = {
    "glass-dark": {
        "bg": "#0b0d12",
        "glass": "rgb(22 25 33 / .74)",
        "glassStrong": "rgb(28 31 41 / .94)",
        "raised": "rgb(255 255 255 / .06)",
        "raisedHover": "rgb(255 255 255 / .11)",
        "line": "rgb(255 255 255 / .1)",
        "text": "#eef1f6",
        "muted": "#9aa1ad",
        "faint": "#6b7280",
        "accent": "#5ac8fa",
        "accent2": "#a78bfa",
        "onAccent": "#06121c",
        "ok": "#4ade80",
        "warn": "#fbbf24",
        "danger": "#f87171",
        "info": "#60a5fa",
        "onStatus": "#071016",
        "slotBot": "#f0abfc",
        "shadow": "rgb(0 0 0 / .45)",
    },
    "glass-light": {
        "bg": "#e9edf3",
        "glass": "rgb(255 255 255 / .78)",
        "glassStrong": "rgb(255 255 255 / .96)",
        "raised": "rgb(15 23 42 / .05)",
        "raisedHover": "rgb(15 23 42 / .09)",
        "line": "rgb(15 23 42 / .12)",
        "text": "#111827",
        "muted": "#4b5563",
        "faint": "#8a93a1",
        "accent": "#0369a1",
        "accent2": "#6d28d9",
        "onAccent": "#ffffff",
        "ok": "#15803d",
        "warn": "#a16207",
        "danger": "#b91c1c",
        "info": "#1d4ed8",
        "onStatus": "#ffffff",
        "slotBot": "#a21caf",
        "shadow": "rgb(15 23 42 / .16)",
    },
    "midnight": {
        "bg": "#000000",
        "glass": "#0d0f14",
        "glassStrong": "#12151c",
        "raised": "#171a22",
        "raisedHover": "#20242e",
        "line": "#262a36",
        "text": "#e7eaf0",
        "muted": "#8a909c",
        "faint": "#5b6170",
        "accent": "#38bdf8",
        "accent2": "#818cf8",
        "onAccent": "#001018",
        "ok": "#22c55e",
        "warn": "#eab308",
        "danger": "#ef4444",
        "info": "#3b82f6",
        "onStatus": "#031008",
        "slotBot": "#e879f9",
        "shadow": "rgb(0 0 0 / .6)",
    },
    "high-contrast": {
        "bg": "#000000",
        "glass": "#000000",
        "glassStrong": "#000000",
        "raised": "#1a1a1a",
        "raisedHover": "#333333",
        "line": "#ffffff",
        "text": "#ffffff",
        "muted": "#e5e5e5",
        "faint": "#c8c8c8",
        "accent": "#ffff00",
        "accent2": "#00ffff",
        "onAccent": "#000000",
        "ok": "#00ff00",
        "warn": "#ffbf00",
        "danger": "#ff6b6b",
        "info": "#00bfff",
        "onStatus": "#000000",
        "slotBot": "#ff80ff",
        "shadow": "rgb(0 0 0 / 0)",
    },
}
BLUR = {"glass-dark": True, "glass-light": True, "midnight": False, "high-contrast": False}
CSS_NAMES = {
    "glass-strong": "glassStrong",
    "raised-hover": "raisedHover",
    "accent-2": "accent2",
    "on-accent": "onAccent",
}

_RGB = re.compile(r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)\s*(?:[/,]\s*([\d.]+)\s*)?\)")
_HEX = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")


def qml_color(value: str) -> str:
    """A CSS colour (`#5ac8fa`, `#fff`, `rgb(22 25 33 / .74)`) as Qt's `#AARRGGBB`; ValueError if it isn't one."""
    text = value.strip()
    found = _RGB.fullmatch(text)
    if found:
        red, green, blue = (int(found.group(index)) for index in (1, 2, 3))
        alpha = float(found.group(4)) if found.group(4) else 1.0
        return f"#{round(alpha * 255):02x}{red:02x}{green:02x}{blue:02x}"
    found = _HEX.fullmatch(text)
    if found:
        digits = found.group(1)
        if len(digits) == 3:
            digits = "".join(digit * 2 for digit in digits)
        if len(digits) == 6:
            return f"#ff{digits.lower()}"
        return f"#{digits[6:].lower()}{digits[:6].lower()}"  # CSS #RRGGBBAA
    raise ValueError(f"not a colour: {value!r}")


def colors(name: str = DEFAULT, custom: Path | None = None) -> dict[str, str]:
    """A theme's tokens as QML colours; a custom theme file is laid over its base."""
    base = name if name in THEMES else DEFAULT
    overrides: dict[str, str] = {}
    if custom is not None and custom.is_file():
        try:
            data = tomllib.loads(custom.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if data.get("base") in THEMES:
            base = str(data["base"])
        for key, value in data.items():
            if key != "base" and isinstance(value, str):
                overrides[CSS_NAMES.get(key, key)] = value
    found = {}
    for key, value in THEMES[base].items():
        found[key] = qml_color(value)
    for key, value in overrides.items():
        try:
            found[key] = qml_color(value)
        except ValueError:
            continue  # a broken custom value keeps the base theme's
    return found


def blurs(name: str) -> bool:
    """Whether the theme draws glass over a blurred background (midnight and high contrast don't)."""
    return BLUR.get(name, True)
