"""Finding a target's image inside a screenshot. Arrays in, matches out; no screen involved.

The default is plain template matching in full colour at the image's own size (OpenCV's TM_CCOEFF_NORMED).
Options change how, per target (its .json's `"match"`) or for the whole bot (`settings.match`); none is on
unless asked for, and each is measured on the test bench (bench/) before it's recommended:

    grayscale   match grey pixels: about a third of the work; colour is ignored
    fast        find candidates on smaller copies of both, then check each at full size
    sizes       when the image isn't found at its own size, try these sizes in turn (True: 0.75 to 1.33)
    colour      a match needs the right colours too: its score is the lower of the shape's and the share of
                its pixels in the right colour (plain matching scores an icon in other colours about as high)

A matcher (this module, or a plugin's: runtime/matchers.py) has `closest` and `every`.
"""

from dataclasses import dataclass

import cv2
import numpy as np

from .geometry import Region
from .placement import resized
from .targets import Match, Target

# `sizes = true`: the common steps between screen sizes, nearest first (the first that scores high enough wins)
DEFAULT_SIZES = (0.9, 1.1, 0.8, 1.25, 0.75, 1.33)
FAST_SMALLEST = 12  # px: the fast pass shrinks the image no smaller than this on its shorter side
FAST_MOST = 4  # the fast pass shrinks by at most this much
FAST_CANDIDATES = 5  # places from the small pass checked at full size
COLOUR_NEAR = 40  # a pixel is in the right colour when its distance from the image's (in BGR) is at most this;
# on the bench, JPEG screens keep at least 93% of pixels this near and an icon in other colours under 10%


@dataclass(frozen=True)
class Options:
    """How to match; everything off is the plain default."""

    grayscale: bool = False
    fast: bool = False
    sizes: tuple[float, ...] = ()
    colour: bool = False

    @classmethod
    def from_dict(cls, values: dict | None) -> "Options":
        """Options from settings or a target's .json: `{"fast": true, "sizes": [0.75, 1.25]}`."""
        if not values:
            return PLAIN
        sizes = values.get("sizes") or ()
        if sizes is True:
            sizes = DEFAULT_SIZES
        return cls(
            grayscale=bool(values.get("grayscale")),
            fast=bool(values.get("fast")),
            sizes=tuple(float(size) for size in sizes),
            colour=bool(values.get("colour")),
        )


PLAIN = Options()


@dataclass
class Spot:
    """Where an image scored best in a haystack, in the haystack's pixels."""

    x: int
    y: int
    w: int
    h: int
    score: float


def scores(image: np.ndarray, haystack: np.ndarray) -> np.ndarray | None:
    """A score from 0 to 1 for every spot the image could sit at; None if it doesn't fit."""
    h, w = image.shape[:2]
    if haystack.shape[0] < h or haystack.shape[1] < w:
        return None
    if float(image.std()) < 1.0:
        # a single-colour image has no pattern to correlate; score by how close the colours are
        channels = 1 if image.ndim == 2 else image.shape[2]
        difference = cv2.matchTemplate(haystack, image, cv2.TM_SQDIFF)
        result = (1 - np.sqrt(difference / (w * h * channels)) / 255).astype(np.float32)
    else:
        result = cv2.matchTemplate(haystack, image, cv2.TM_CCOEFF_NORMED)
    result[~np.isfinite(result)] = 0
    return result


def best(
    target: Target, haystack: np.ndarray, origin: Region, similarity: float, options: Options = PLAIN
) -> Match | None:
    """The best spot for the target in `haystack` (which sits at `origin` on screen), if it scores high enough."""
    found = closest(target, haystack, origin, similarity, options)
    if found is None or found.score < similarity:
        return None
    return found


def closest(
    target: Target, haystack: np.ndarray, origin: Region, enough: float, options: Options = PLAIN
) -> Match | None:
    """The best spot for the target whatever it scores; with `sizes`, other sizes are tried until one scores
    `enough`. None only when the image doesn't fit in the haystack."""
    found = _best_at_size(target.pixels, haystack, options)
    if options.sizes and (found is None or found.score < enough):
        for size in options.sizes:
            other = _best_at_size(resized(target.pixels, size), haystack, options)
            if other is not None and (found is None or other.score > found.score):
                found = other
            if found is not None and found.score >= enough:
                break
    if found is None:
        return None
    return Match(origin.x + found.x, origin.y + found.y, found.w, found.h, float(found.score), target)


def every(
    target: Target,
    haystack: np.ndarray,
    origin: Region,
    similarity: float,
    limit: int = 100,
    options: Options = PLAIN,
) -> list[Match]:
    """Every spot scoring high enough, best first, without overlapping each other (at the image's own size)."""
    image = target.pixels
    result = scores(_grey(image) if options.grayscale else image, _grey(haystack) if options.grayscale else haystack)
    if result is None:
        return []
    h, w = image.shape[:2]
    found = []
    while len(found) < limit:
        _, score, _, (x, y) = cv2.minMaxLoc(result)
        if score < similarity:
            break
        # blank out this spot and anything that would overlap it
        result[max(0, y - h + 1) : y + h, max(0, x - w + 1) : x + w] = -1
        if options.colour:
            score = min(score, colour_score(image, haystack[y : y + h, x : x + w]))
            if score < similarity:
                continue
        found.append(Match(origin.x + x, origin.y + y, w, h, float(score), target))
    return found


def _best_at_size(image: np.ndarray, haystack: np.ndarray, options: Options) -> Spot | None:
    picture = image
    space = haystack
    if options.grayscale:
        picture = _grey(image)
        space = _grey(haystack)
    if options.fast:
        spot = _fast(picture, space)
    else:
        spot = _plain(picture, space)
    if spot is not None and options.colour:
        patch = haystack[spot.y : spot.y + spot.h, spot.x : spot.x + spot.w]
        spot.score = min(spot.score, colour_score(image, patch))
    return spot


def _plain(image: np.ndarray, haystack: np.ndarray) -> Spot | None:
    result = scores(image, haystack)
    if result is None:
        return None
    _, score, _, (x, y) = cv2.minMaxLoc(result)
    h, w = image.shape[:2]
    return Spot(x, y, w, h, float(score))


def _fast(image: np.ndarray, haystack: np.ndarray) -> Spot | None:
    """Candidates from smaller copies of both, each checked at full size in a small window around it."""
    h, w = image.shape[:2]
    shrink = min(FAST_MOST, min(h, w) // FAST_SMALLEST)
    if shrink < 2:
        return _plain(image, haystack)
    small_image = cv2.resize(image, (w // shrink, h // shrink), interpolation=cv2.INTER_AREA)
    small_haystack = cv2.resize(
        haystack, (haystack.shape[1] // shrink, haystack.shape[0] // shrink), interpolation=cv2.INTER_AREA
    )
    result = scores(small_image, small_haystack)
    if result is None:
        return _plain(image, haystack)
    small_h, small_w = small_image.shape[:2]
    found: Spot | None = None
    for _ in range(FAST_CANDIDATES):
        _, _, _, (x, y) = cv2.minMaxLoc(result)
        result[max(0, y - small_h + 1) : y + small_h, max(0, x - small_w + 1) : x + small_w] = -1
        left = max(0, x * shrink - shrink * 2)
        top = max(0, y * shrink - shrink * 2)
        window = haystack[top : top + h + shrink * 4, left : left + w + shrink * 4]
        spot = _plain(image, window)
        if spot is not None and (found is None or spot.score > found.score):
            found = Spot(left + spot.x, top + spot.y, w, h, spot.score)
    return found


def colour_score(image: np.ndarray, patch: np.ndarray) -> float:
    """The share of pixels, 0 to 1, whose colour in `patch` is near the image's (two same-sized pictures)."""
    if patch.shape != image.shape or image.ndim < 3:
        return 1.0
    difference = image.astype(np.int32) - patch.astype(np.int32)
    distance = (difference * difference).sum(axis=2)
    return float((distance <= COLOUR_NEAR * COLOUR_NEAR).mean())


def _grey(pixels: np.ndarray) -> np.ndarray:
    if pixels.ndim == 2:
        return pixels
    return cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
