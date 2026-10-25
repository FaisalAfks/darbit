"""The hub's requests: projects, running bots, the library and run history. See docs/tasks/T20-hub.md."""


def projects_list(data: dict) -> list[dict]:
    """Installed bots: name, path, accent, status, last run."""
    raise NotImplementedError("TODO(T20)")


def project_run(data: dict) -> dict:
    """Start a bot as a child process in its venv, with DARBIT_SERVER set so it publishes here."""
    raise NotImplementedError("TODO(T20)")


def project_stop(data: dict) -> dict:
    raise NotImplementedError("TODO(T20)")


def library_list(data: dict) -> list[dict]:
    """Every target with a cached 96 px thumbnail, kind, region link and last score."""
    raise NotImplementedError("TODO(T20)")
