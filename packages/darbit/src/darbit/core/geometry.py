"""Points and rectangles in real screen pixels."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    """A point on the screen."""

    x: float
    y: float

    def moved(self, dx: float, dy: float) -> "Location":
        return Location(self.x + dx, self.y + dy)

    def point(self) -> tuple[int, int]:
        return round(self.x), round(self.y)


@dataclass(frozen=True)
class Region:
    """A rectangle on the screen."""

    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def center(self) -> Location:
        return Location(self.x + self.w / 2, self.y + self.h / 2)

    def moved(self, dx: int, dy: int) -> "Region":
        return Region(self.x + dx, self.y + dy, self.w, self.h)

    def grow(self, pixels: int) -> "Region":
        return Region(self.x - pixels, self.y - pixels, self.w + 2 * pixels, self.h + 2 * pixels)

    def contains(self, where: Location) -> bool:
        return self.x <= where.x < self.right and self.y <= where.y < self.bottom

    def intersect(self, other: "Region") -> "Region | None":
        left, top = max(self.x, other.x), max(self.y, other.y)
        right, bottom = min(self.right, other.right), min(self.bottom, other.bottom)
        if right <= left or bottom <= top:
            return None
        return Region(left, top, right - left, bottom - top)
