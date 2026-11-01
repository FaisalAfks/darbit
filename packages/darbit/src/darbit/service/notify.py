"""Notifications from darbit's service to a phone: a bot failed, ended or is stuck, and a daily summary.

Set in notify.toml in darbit's settings folder (%APPDATA%\\darbit on Windows); any of the three channels:

    [ntfy]
    topic = "my-darbit-1234"          # ntfy.sh, or `server = "https://..."` for your own
    [discord]
    webhook = "https://discord.com/api/webhooks/..."
    [telegram]
    token = "123:ABC"
    chat = "123456"

    [when]
    failed = true                     # these are the defaults
    ended = false                     # a bot stopping on its own or from the Studio
    stuck_minutes = 15                # running, with nothing in its report for this long; 0 is off
    summary = "23:30"                 # each bot that ran today; "" is off

Sending never raises and never holds up the service: each message goes on its own thread.
"""

import json
import threading
import time
import tomllib
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .. import events, paths
from ..project.manifest import ProjectError, load
from ..server import hub, results

FILE = "notify.toml"
SEND_WAIT = 10.0  # seconds for a channel to take a message
LOOK_EVERY = 30.0  # seconds between looks for stuck bots and the summary's time
TITLE = "darbit"


@dataclass
class Channel:
    name: str
    url: str
    body: Callable[[str, str], tuple[bytes, str]]  # (title, text) -> (data, content type)


@dataclass
class Settings:
    channels: list[Channel] = field(default_factory=list)
    failed: bool = True
    ended: bool = False
    stuck_minutes: float = 15
    summary: str = "23:30"


def settings_file() -> Path:
    return paths.config_dir() / FILE


def load_settings(path: Path | None = None) -> Settings:
    """The notification settings; no channels when the file is missing or broken."""
    try:
        data = tomllib.loads((path or settings_file()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    found = Settings()
    found.channels = _channels(data)
    when = data.get("when", {})
    if isinstance(when, dict):
        found.failed = bool(when.get("failed", found.failed))
        found.ended = bool(when.get("ended", found.ended))
        found.stuck_minutes = float(when.get("stuck_minutes", found.stuck_minutes))
        found.summary = str(when.get("summary", found.summary))
    return found


def _channels(data: dict) -> list[Channel]:
    found = []
    ntfy = data.get("ntfy")
    if isinstance(ntfy, dict) and ntfy.get("topic"):
        server = str(ntfy.get("server", "https://ntfy.sh")).rstrip("/")
        found.append(Channel("ntfy", f"{server}/{ntfy['topic']}", _ntfy_body))
    discord = data.get("discord")
    if isinstance(discord, dict) and discord.get("webhook"):
        found.append(Channel("discord", str(discord["webhook"]), _discord_body))
    telegram = data.get("telegram")
    if isinstance(telegram, dict) and telegram.get("token") and telegram.get("chat"):
        url = f"https://api.telegram.org/bot{telegram['token']}/sendMessage"
        chat = str(telegram["chat"])
        found.append(Channel("telegram", url, lambda title, text: _telegram_body(chat, title, text)))
    return found


def _ntfy_body(title: str, text: str) -> tuple[bytes, str]:
    return f"{title}\n{text}".encode(), "text/plain; charset=utf-8"


def _discord_body(title: str, text: str) -> tuple[bytes, str]:
    return json.dumps({"content": f"**{title}**\n{text}"}).encode(), "application/json"


def _telegram_body(chat: str, title: str, text: str) -> tuple[bytes, str]:
    return json.dumps({"chat_id": chat, "text": f"{title}\n{text}"}).encode(), "application/json"


def send(channels: list[Channel], title: str, text: str) -> None:
    """Send to every channel, each on its own thread."""
    for channel in channels:
        threading.Thread(target=post, args=(channel, title, text), name=f"darbit-notify-{channel.name}").start()


def post(channel: Channel, title: str, text: str) -> bool:
    """Send one message to one channel now; whether it got there."""
    data, kind = channel.body(title, text)
    request = urllib.request.Request(channel.url, data=data, headers={"Content-Type": kind}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=SEND_WAIT):
            return True
    except OSError:
        return False  # a phone missing one message mustn't stop the service


class Notifier:
    """Listens to the service's events and sends what notify.toml asks for."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.last_change: dict[str, float] = {}  # bot folder -> when its report last changed (monotonic)
        self.stuck_told: set[str] = set()
        self.summary_sent = ""  # the day the summary went
        self.running = threading.Event()
        self.stop_listening: Callable[[], None] | None = None

    def start(self) -> None:
        if not self.settings.channels:
            return
        self.stop_listening = events.listen(self.on_event)
        self.running.set()
        threading.Thread(target=self._look, name="darbit-notify", daemon=True).start()

    def stop(self) -> None:
        self.running.clear()
        if self.stop_listening is not None:
            self.stop_listening()

    def on_event(self, topic: str, data: dict) -> None:
        folder = str(data.get("path", ""))
        if topic == "project.changed":
            self.last_change[folder] = time.monotonic()
            self.stuck_told.discard(folder)
        elif topic == "project.status":
            status = data.get("status")
            if status == "running":
                self.last_change[folder] = time.monotonic()
            elif status == "failed" and self.settings.failed:
                self.tell(f"{_name(folder)} failed", _last_problem(folder) + _restarting(data))
            elif status == "stopped" and self.settings.ended:
                self.tell(f"{_name(folder)} stopped", "")

    def tell(self, title: str, text: str) -> None:
        send(self.settings.channels, title, text)

    def look_now(self, now: datetime | None = None) -> None:
        """Tell about stuck bots, and send the summary once its time has come."""
        self._stuck()
        moment = now or datetime.now()
        day = moment.strftime("%Y-%m-%d")
        if self.settings.summary and moment.strftime("%H:%M") >= self.settings.summary and self.summary_sent != day:
            self.summary_sent = day
            text = summary(day)
            if text:
                self.tell(f"darbit, {day}", text)

    def _stuck(self) -> None:
        if self.settings.stuck_minutes <= 0:
            return
        for folder in hub.running():
            key = str(folder)
            changed = self.last_change.setdefault(key, time.monotonic())
            if key in self.stuck_told or time.monotonic() - changed < self.settings.stuck_minutes * 60:
                continue
            self.stuck_told.add(key)
            minutes = round(self.settings.stuck_minutes)
            self.tell(f"{folder.name} may be stuck", f"nothing in its report for {minutes} minutes")

    def _look(self) -> None:
        while self.running.is_set():
            self.look_now()
            time.sleep(LOOK_EVERY)


def summary(day: str) -> str:
    """Each bot that ran on `day`: its steps, gains and problems, a few lines each."""
    parts = []
    for folder in hub.project_folders():
        try:
            project = load(folder)
            found = results.day(project, day)
        except (ProjectError, OSError, ValueError):
            continue
        if found.get("start") is None:
            continue
        lines = results.day_lines(found)
        parts.append("\n".join([project.name, *lines[1:]]))
    return "\n\n".join(parts)


def _name(folder: str) -> str:
    try:
        return load(Path(folder)).name
    except (ProjectError, OSError):
        return Path(folder).name


def _restarting(data: dict) -> str:
    """What the service does about a failure, when the bot has [run] restart."""
    if "restart" not in data:
        return ""
    if data["restart"]:
        return f"\nStarting it again in a few seconds ({data['restart']} of {data['restarts']} this hour)."
    return f"\nIt failed {data['restarts']} times this hour already: left stopped."


def _last_problem(folder: str) -> str:
    """The last failed step in today's results, for a failure's message."""
    try:
        found = results.day(load(Path(folder)), datetime.now().strftime("%Y-%m-%d"))
    except (ProjectError, OSError, ValueError):
        return ""
    problems = found.get("problems") or []
    if not problems:
        return "it ended with an error: see its log"
    last = problems[-1]
    return f"{last['step']}: {last['reason']}"
