"""A window for the live tests to work on: it shows a picture and writes down every click and key it gets.

    python target.py picture.png events.jsonl

Each line of events.jsonl is one thing that happened, with `t` from time.perf_counter() (the same clock in every
process on Windows) and places in screen pixels. The first line says where the window's client area is.
"""

import json
import sys
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QWidget

TITLE = "darbit live target"
PICTURE = "live_patch"  # the picture conftest.py makes
PICTURE_AT = (120, 90)  # where the picture is in the client area


class Target(QWidget):
    def __init__(self, picture: str, out: str) -> None:
        super().__init__()
        self.out = open(out, "a", encoding="utf-8")  # noqa: SIM115 - open for the window's whole life
        self.setWindowTitle(TITLE)
        self.setStyleSheet("background: #20242c;")
        self.setGeometry(200, 160, 640, 420)
        label = QLabel(self)
        label.setPixmap(QPixmap(picture))
        label.move(*PICTURE_AT)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def write(self, **data: object) -> None:
        data["t"] = time.perf_counter()
        self.out.write(json.dumps(data) + "\n")
        self.out.flush()

    def ready(self) -> None:
        corner = self.mapToGlobal(self.rect().topLeft())
        self.write(kind="ready", x=corner.x(), y=corner.y(), w=self.width(), h=self.height())

    def mousePressEvent(self, event) -> None:
        spot = event.globalPosition().toPoint()
        self.write(kind="click", button=event.button().name, x=spot.x(), y=spot.y())

    def mouseReleaseEvent(self, event) -> None:
        self.write(kind="release", button=event.button().name)

    def keyPressEvent(self, event) -> None:
        if not event.isAutoRepeat():
            self.write(kind="key", text=event.text(), code=event.nativeScanCode())

    def keyReleaseEvent(self, event) -> None:
        if not event.isAutoRepeat():
            self.write(kind="key_up", text=event.text(), code=event.nativeScanCode())


def main() -> int:
    app = QApplication([sys.argv[0], "-platform", "windows:dpiawareness=2"])
    window = Target(sys.argv[1], sys.argv[2])
    window.show()
    window.raise_()
    window.activateWindow()
    QTimer.singleShot(500, window.ready)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
