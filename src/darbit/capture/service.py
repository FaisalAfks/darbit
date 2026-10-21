"""The capture tool's requests on the local server. See docs/tasks/T09-capture-overlay.md and T10.

Registered with server.app.handles when the server starts; nothing here imports the server.
"""
from __future__ import annotations


def freeze(data: dict) -> dict:
    """Grab the monitors, start engine.prepare() on each, send the frames, then capture.lines events."""
    raise NotImplementedError("TODO(T09)")


def candidates(data: dict) -> list[list[int]]:
    """engine.candidates for {x, y, kind} on the current frozen frame."""
    raise NotImplementedError("TODO(T09)")


def targets(data: dict) -> list[dict]:
    """The project's saved targets: name, kind, box, region (name or box), offset, thumbnail."""
    raise NotImplementedError("TODO(T09)")


def save(data: dict) -> dict:
    """Write a draft's .png and .json with store.save_result; returns undo data."""
    raise NotImplementedError("TODO(T09)")


def undo(data: dict) -> dict:
    raise NotImplementedError("TODO(T10)")


def redo(data: dict) -> dict:
    raise NotImplementedError("TODO(T10)")


def rename(data: dict) -> dict:
    """Move a target's files and update region links that name it."""
    raise NotImplementedError("TODO(T10)")


def delete(data: dict) -> dict:
    raise NotImplementedError("TODO(T10)")
