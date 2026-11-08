"""The refusal of the one-input-bot rule (decision 0020): a bot start, an action's play or a recording refused
because a bot, an action playing or a recording uses the mouse and keys. Kept apart from hub.py so the input
worker can answer with it without loading the hub.
"""


class InputBotRunning(ValueError):
    """Refused: a bot, an action or a recording that uses the mouse and keys is on. `starting` says what was refused
    ("start my-bot", "play go_to_boss"); `replace` whether doing it again with replace would stop the others."""

    code = "input_bot_running"

    def __init__(self, starting: str, running: list[dict], replace: bool = True) -> None:
        names = ", ".join(_called(bot) for bot in running)
        then = f"stop it first, or {starting} with replace"
        if not replace:
            then = f"stop it to {starting}"
        if recording_in(running):
            then = f"finish or cancel the recording to {starting} (replace doesn't stop a recording)"
        super().__init__(f"{names} is running and uses the mouse and keys too: {then}")
        self.running = running

    def detail(self) -> dict:
        return {"running": self.running}


def recording_in(running: list[dict]) -> bool:
    """Whether one of them is a recording, which nothing but the person recording ends."""
    for bot in running:
        if bot.get("status") == "recording":
            return True
    return False


def _called(bot: dict) -> str:
    """A bot's name, "my-bot's action go_to_boss" for an action playing, or "a recording of my-bot's action run"."""
    if bot.get("status") == "recording":
        return f"a recording of {bot['name']}'s action {bot['action']}"
    if "action" in bot:
        return f"{bot['name']}'s action {bot['action']}"
    return bot["name"]
