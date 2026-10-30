"""Capturing targets from a frozen screen: the session (service.py), what's saved (store.py), setup guides
(guide.py), the box-finding engine (engine/), and capture lists (common.py).

The capture windows that used this were v0.4's web Studio and the older Tk tool; both are gone from main
(decision 0015). The new Studio's Capture (milestone 4 of the rebuild plan) builds on these modules.
"""

from .common import distinct

__all__ = ["distinct"]
