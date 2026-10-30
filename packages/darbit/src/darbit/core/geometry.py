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


@dataclass(frozen=True, eq=False)
class Region:
    """A rectangle on the screen. `d.Region` (runtime/region.py) is this with the searches and clicks added; the
    two are equal when their numbers are."""

    x: int
    y: int
    w: int
    h: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Region):
            return NotImplemented
        return (self.x, self.y, self.w, self.h) == (other.x, other.y, other.w, other.h)

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.w, self.h))

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
        return type(self)(self.x + dx, self.y + dy, self.w, self.h)

    def grow(self, pixels: int) -> "Region":
        return type(self)(self.x - pixels, self.y - pixels, self.w + 2 * pixels, self.h + 2 * pixels)

    def contains(self, where: Location) -> bool:
        return self.x <= where.x < self.right and self.y <= where.y < self.bottom

    def intersect(self, other: "Region") -> "Region | None":
        left, top = max(self.x, other.x), max(self.y, other.y)
        right, bottom = min(self.right, other.right), min(self.bottom, other.bottom)
        if right <= left or bottom <= top:
            return None
        return type(self)(left, top, right - left, bottom - top)
