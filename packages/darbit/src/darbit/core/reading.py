"""Reading text in pixels: what a reader gives back, the characters a read may use, preparing the pixels, and turning
the text into a number or a time. Arrays and strings in, results out; no screen and no model involved.

A reader (core/rapid.py, or a plugin's: runtime/readers.py) recognises the text; this module holds what every reader
shares. The preparing options (upscale, invert, threshold) are off unless asked for (decision 0019), like the matching
options.
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import cv2
import numpy as np

DIGITS = "0123456789"
# what `"text": "<name>"` in a Region's .json, or `chars=`, stands for; any other string is the characters themselves
CHARACTER_SETS = {
    "digits": DIGITS,
    "number": DIGITS + ".,%+-kKmMbBtT",
    "time": DIGITS + ":.hmsd ",
}

UPSCALE = 2.0  # `upscale = true`: twice the size, for text a few pixels high
TRIM_CONTRAST = 60  # grey levels a pixel's neighbourhood must span to be an edge of the text
TRIM_PIXELS = 2  # edge pixels a row or column needs to hold text (one is noise)
TRIM_MARGIN = 4  # px kept around the text when a single line is trimmed


@dataclass(frozen=True)
class Reading:
    """Text a reader saw, and how sure it is, 0 to 1."""

    text: str
    confidence: float


@dataclass(frozen=True)
class Prepare:
    """How to prepare pixels before reading and how to read them; the defaults read one line, cut to its text."""

    upscale: float = 1.0  # resize by this much first
    invert: bool = False  # dark text on a light background becomes light on dark
    threshold: int | None = None  # 0: black and white by Otsu's method; 1 to 255: a fixed grey level
    lines: bool = False  # find each line of text first (several lines, or text with a lot around it)
    trim: bool = True  # a single line is cut to its text first (on the bench, a loose Region misreads without it)

    @classmethod
    def from_dict(cls, values: dict | None) -> "Prepare":
        """Options from settings or a Region's .json: `{"upscale": 3, "invert": true, "threshold": true}`."""
        if not values:
            return PLAIN
        upscale = values.get("upscale") or 1.0
        if upscale is True:
            upscale = UPSCALE
        threshold = values.get("threshold")
        if threshold is True:
            threshold = 0
        elif threshold is False:
            threshold = None
        return cls(
            upscale=float(upscale),
            invert=bool(values.get("invert")),
            threshold=None if threshold is None else int(threshold),
            lines=bool(values.get("lines")),
            trim=bool(values.get("trim", True)),
        )


PLAIN = Prepare()


def characters(chars: str | None) -> str | None:
    """The characters a read may give: a set's name ("digits", "number", "time") or the characters themselves;
    None for any."""
    if not chars:
        return None
    return CHARACTER_SETS.get(chars, chars)


def prepare(pixels: np.ndarray, how: Prepare) -> np.ndarray:
    """The pixels as the options say (BGR in, BGR out)."""
    if how.upscale != 1.0:
        pixels = cv2.resize(pixels, None, fx=how.upscale, fy=how.upscale, interpolation=cv2.INTER_CUBIC)
    if how.invert:
        pixels = 255 - pixels
    if how.threshold is not None:
        grey = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
        if how.threshold == 0:
            _, black_white = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            _, black_white = cv2.threshold(grey, how.threshold, 255, cv2.THRESH_BINARY)
        pixels = cv2.cvtColor(black_white, cv2.COLOR_GRAY2BGR)
    return np.ascontiguousarray(pixels)


def trim(pixels: np.ndarray) -> np.ndarray:
    """The pixels cut to the text in them, a few pixels around it: a recogniser sees one line squeezed to its own
    height, so empty space around small text shrinks the text. Text is where the grey level changes sharply (its
    edges), which a smooth or gently noisy background doesn't. Unchanged when nothing stands out."""
    grey = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY) if pixels.ndim == 3 else pixels
    if grey.shape[0] < 3 or grey.shape[1] < 3:
        return pixels
    smooth = cv2.GaussianBlur(grey, (3, 3), 0)
    edges = cv2.morphologyEx(smooth, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    text = edges > TRIM_CONTRAST
    rows = np.flatnonzero(text.sum(axis=1) >= TRIM_PIXELS)
    columns = np.flatnonzero(text.sum(axis=0) >= TRIM_PIXELS)
    if rows.size == 0 or columns.size == 0:
        return pixels
    top = max(int(rows[0]) - TRIM_MARGIN, 0)
    bottom = min(int(rows[-1]) + TRIM_MARGIN + 1, grey.shape[0])
    left = max(int(columns[0]) - TRIM_MARGIN, 0)
    right = min(int(columns[-1]) + TRIM_MARGIN + 1, grey.shape[1])
    return np.ascontiguousarray(pixels[top:bottom, left:right])


def decode(chances: np.ndarray, alphabet: list[str], allowed: str | None = None) -> Reading:
    """Text from a recogniser's chances per step and character (CTC, best path), using only the allowed characters.

    `alphabet[0]` is the blank between characters. Leaving characters out before choosing (instead of dropping them
    after) lets a 0 win where an O was a little likelier."""
    if allowed is not None:
        keep = np.zeros(len(alphabet), dtype=bool)
        keep[0] = True
        for index, character in enumerate(alphabet):
            if character in allowed:
                keep[index] = True
        chances = np.where(keep, chances, 0.0)
    best = chances.argmax(axis=1)
    sure = chances.max(axis=1)
    text = []
    scores = []
    previous = -1
    for step, index in enumerate(best):
        if index != 0 and index != previous:
            text.append(alphabet[index])
            scores.append(float(sure[step]))
        previous = index
    if not text:
        return Reading("", 0.0)
    return Reading("".join(text), sum(scores) / len(scores))


SUFFIXES = {"k": 3, "m": 6, "b": 9, "t": 12}  # 4.99M: millions
NUMBER = re.compile(r"[+-]?\d+(\.\d+)?")
THOUSANDS = re.compile(r"\d{1,3}(,\d{3})+(\.\d+)?")  # 1,234 or 12,345.6


def parse_number(text: str | None) -> float | None:
    """A number as a game shows it: `1,234`, `4.99M`, `126.62B`, `1.5k`, `12%` (12.0), `-3`. None if it isn't one."""
    if text is None:
        return None
    clean = text.strip().replace(" ", "")
    clean = clean.removesuffix("%")
    exponent = 0
    if clean and clean[-1].lower() in SUFFIXES:
        exponent = SUFFIXES[clean[-1].lower()]
        clean = clean[:-1]
    if THOUSANDS.fullmatch(clean.lstrip("+-")):
        clean = clean.replace(",", "")
    else:
        clean = clean.replace(",", ".")  # 1,5: a decimal comma
    if not NUMBER.fullmatch(clean):
        return None
    try:
        value = Decimal(clean).scaleb(exponent)  # exact: 4.99M is 4990000, not 4990000.000000001
    except InvalidOperation:
        return None
    return float(value)


CLOCK = re.compile(r"\d{1,3}(:\d{1,2}){1,2}(\.\d+)?")  # 02:31, 1:02:03, 02:31.5
UNIT = re.compile(r"(\d+(?:\.\d+)?)([dhms])")
UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def parse_time(text: str | None) -> float | None:
    """Seconds in a time as a game shows it: `02:31`, `1:02:03`, `2m 30s`, `45s`, `1h 5m`, `1d 2h`. None if it
    isn't one."""
    if text is None:
        return None
    clean = text.strip().lower().replace(" ", "")
    if CLOCK.fullmatch(clean):
        seconds = 0.0
        for part in clean.split(":"):
            seconds = seconds * 60 + float(part)
        return seconds
    if not clean or UNIT.sub("", clean):
        return None  # empty, or something besides numbers with units
    seconds = 0.0
    for amount, unit in UNIT.findall(clean):
        seconds += float(amount) * UNIT_SECONDS[unit]
    return seconds
