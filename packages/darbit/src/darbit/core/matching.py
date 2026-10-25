"""Finding a target's image inside a screenshot. Arrays in, matches out; no screen involved."""

from __future__ import annotations

import cv2
import numpy as np

from .geometry import Region
from .targets import Match, Target


def scores(image: np.ndarray, haystack: np.ndarray) -> np.ndarray | None:
    """A score from 0 to 1 for every spot the image could sit at; None if it doesn't fit."""
    h, w = image.shape[:2]
    if haystack.shape[0] < h or haystack.shape[1] < w:
        return None
    if float(image.std()) < 1.0:
        # a single-colour image has no pattern to correlate; score by how close the colours are
        difference = cv2.matchTemplate(haystack, image, cv2.TM_SQDIFF)
        result = (1 - np.sqrt(difference / (w * h * 3)) / 255).astype(np.float32)
    else:
        result = cv2.matchTemplate(haystack, image, cv2.TM_CCOEFF_NORMED)
    result[~np.isfinite(result)] = 0
    return result


def best(target: Target, haystack: np.ndarray, origin: Region, similarity: float) -> Match | None:
    """The best spot for the target in `haystack` (which sits at `origin` on screen), if it scores high enough."""
    result = scores(target.pixels, haystack)
    if result is None:
        return None
    _, score, _, (x, y) = cv2.minMaxLoc(result)
    if score < similarity:
        return None
    h, w = target.pixels.shape[:2]
    return Match(origin.x + x, origin.y + y, w, h, float(score), target)


def every(target: Target, haystack: np.ndarray, origin: Region, similarity: float, limit: int = 100) -> list[Match]:
    """Every spot scoring high enough, best first, without overlapping each other."""
    result = scores(target.pixels, haystack)
    if result is None:
        return []
    h, w = target.pixels.shape[:2]
    found = []
    while len(found) < limit:
        _, score, _, (x, y) = cv2.minMaxLoc(result)
        if score < similarity:
            break
        found.append(Match(origin.x + x, origin.y + y, w, h, float(score), target))
        # blank out this spot and anything that would overlap it
        result[max(0, y - h + 1) : y + h, max(0, x - w + 1) : x + w] = -1
    return found
