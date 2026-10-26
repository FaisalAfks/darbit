"""Images between the server and the windows, as binary WebSocket frames.

A frame is 4 bytes (big-endian) with the header's length, the header as JSON, then the image bytes:
    {"type": "frame", "id": 7, "w": 2560, "h": 1600, "format": "rgba"} + bytes
Screens go as raw RGBA, ready for the browser's ImageData: the server and the windows are on the same PC, so
sending 16 MB beats encoding it (2560 x 1600: about 12 ms raw, 258 ms as PNG, 1.4 s as lossless WebP). Small
images (thumbnails) go as PNG. Both keep the exact pixels. packages/ui/src/lib/api.ts reads them.
"""

import json
import struct
from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class Frame:
    """An image to send, with what the window needs to know about it."""

    data: bytes
    w: int
    h: int
    format: str = "rgba"  # "rgba": w * h * 4 bytes; "png": a PNG file
    extra: dict = field(default_factory=dict)  # e.g. the monitor it came from

    def header(self, request: int | None) -> dict:
        header = {"type": "frame", "id": request, "w": self.w, "h": self.h, "format": self.format}
        header.update(self.extra)
        return header


def encode(pixels: np.ndarray, extra: dict | None = None, format: str = "rgba") -> Frame:
    """BGR pixels as a frame: raw RGBA (screens) or PNG (small images)."""
    height, width = pixels.shape[:2]
    if format == "rgba":
        data = cv2.cvtColor(pixels, cv2.COLOR_BGR2RGBA).tobytes()
    elif format == "png":
        ok, encoded = cv2.imencode(".png", pixels, [cv2.IMWRITE_PNG_COMPRESSION, 1])
        if not ok:
            raise ValueError("couldn't encode the image as PNG")
        data = encoded.tobytes()
    else:
        raise ValueError(f"unknown frame format {format!r}")
    return Frame(data, width, height, format, extra or {})


def decode(frame_header: dict, data: bytes) -> np.ndarray:
    """A frame's image back as BGR pixels (for tests and tools)."""
    if frame_header["format"] == "rgba":
        rgba = np.frombuffer(data, np.uint8).reshape(frame_header["h"], frame_header["w"], 4)
        return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


def pack(header: dict, data: bytes) -> bytes:
    """A binary WebSocket message: header length, header, image."""
    text = json.dumps(header).encode("utf-8")
    return struct.pack(">I", len(text)) + text + data


def unpack(message: bytes) -> tuple[dict, bytes]:
    """The header and the image bytes of a binary message, as pack made it."""
    (length,) = struct.unpack(">I", message[:4])
    header = json.loads(message[4 : 4 + length].decode("utf-8"))
    return header, message[4 + length :]
