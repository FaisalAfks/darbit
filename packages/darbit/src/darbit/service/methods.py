"""What a client can ask darbit's service: each method's name, what it does and the function that does it.

Methods about one bot take `bot`: its name, its folder's name or its path. Everything else in `params` goes to
the handler as it came. The handlers are server/hub.py's, which the old Studio used too.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..server import actions_api, hub


@dataclass(frozen=True)
class Method:
    run: Callable[[dict], object]
    about: str
    one_bot: bool = True  # takes `bot`


def _bots_add(params: dict) -> object:
    return hub.project_add({"path": params.get("path", "")})


def _bots_new(params: dict) -> object:
    """A new bot from darbit's template, in darbit's bots folder (or `where`)."""
    from .. import paths
    from ..project import bots

    where = Path(str(params.get("where") or paths.bots_dir())).expanduser()
    where.mkdir(parents=True, exist_ok=True)
    try:
        folder = bots.new(str(params.get("name", "")).strip(), where)
    except FileExistsError as error:
        raise ValueError(f"{error.filename or 'that folder'} already exists") from error
    if folder.parent != paths.bots_dir():
        hub.project_add({"path": str(folder)})
    return hub.describe(folder)


def _bots_install(params: dict) -> object:
    """Install a bot from its git link into darbit's bots folder."""
    import subprocess

    from ..project import bots

    try:
        folder = bots.install(str(params.get("url", "")).strip())
    except (FileExistsError, RuntimeError) as error:
        raise ValueError(str(error)) from error
    except subprocess.CalledProcessError as error:
        raise ValueError(f"{' '.join(error.cmd)} failed (exit code {error.returncode})") from error
    return hub.describe(folder)


def _actions(params: dict) -> object:
    return actions_api.listing(Path(params["path"]))


def _action_read(params: dict) -> object:
    return actions_api.read(Path(params["path"]), str(params.get("name", "")))


def _action_save(params: dict) -> object:
    sections = params.get("sections")
    if not isinstance(sections, list):
        raise ValueError("an action is saved from its `sections`")  # noqa: TRY004 - the service answers ValueError as a refusal
    return actions_api.save(
        Path(params["path"]), str(params.get("name", "")), sections, str(params.get("docstring", ""))
    )


def _action_stop(params: dict) -> object:
    return actions_api.control("stop")


def _action_resume(params: dict) -> object:
    return actions_api.control("resume")


def _action_step(params: dict) -> object:
    return actions_api.control("step")


def _action_breakpoints(params: dict) -> object:
    lines = [int(line) for line in params.get("lines", [])]
    return actions_api.set_breakpoints(Path(params["path"]), str(params.get("name", "")), lines)


def _action_rename(params: dict) -> object:
    return actions_api.rename(Path(params["path"]), str(params.get("name", "")), str(params.get("to", "")))


def _action_delete(params: dict) -> object:
    return actions_api.delete(Path(params["path"]), str(params.get("name", "")))


def _bot_status(params: dict) -> object:
    return hub.describe(Path(params["path"]))


METHODS: dict[str, Method] = {
    "bots.list": Method(hub.projects_list, "every bot: installed ones and added project folders", one_bot=False),
    "bots.running": Method(hub.bots_running, "the bots running or paused, each with `input`", one_bot=False),
    "inputs.running": Method(
        hub.inputs_running,
        "what sends input now: input bots running or paused, the action playing, the recording on",
        one_bot=False,
    ),
    "bots.add": Method(_bots_add, "add a project folder (`path`)", one_bot=False),
    "bots.new": Method(_bots_new, "make a bot from the template (`name`, `where`)", one_bot=False),
    "bots.install": Method(_bots_install, "install a bot from its git link (`url`)", one_bot=False),
    "bot.status": Method(_bot_status, "one bot: name, version, running, paused or stopped"),
    "bot.start": Method(
        hub.project_run,
        "start a bot in its own process; refused (input_bot_running) while another input bot or an action plays, "
        "unless `replace`",
    ),
    "bot.pause": Method(hub.project_pause, "pause a running bot, or go on"),
    "bot.doctor": Method(hub.project_doctor, "darbit doctor's checks: is the bot ready to start"),
    "bot.stop": Method(hub.project_stop, "stop a bot (it lets go of every key); end it if it doesn't stop in time"),
    "bot.dashboard": Method(hub.dashboard_tiles, "the bot's Overview tiles (`day`, today by default)"),
    "bot.overview": Method(hub.overview_blocks, "the bot's Overview as blocks: catalog, layout and data (`day`)"),
    "bot.settings": Method(hub.settings_get, "the bot's settings: schema and values"),
    "bot.settings.save": Method(hub.settings_save, "save the bot's settings (`values`)"),
    "bot.library": Method(hub.library_list, "the bot's pictures, points and areas"),
    "bot.library.uses": Method(hub.library_uses, "where a picture is used (`name`)"),
    "bot.library.screens": Method(hub.library_screens, "the screens the bot saved"),
    "bot.library.rename_plan": Method(hub.library_rename_plan, "what renaming a picture would change"),
    "bot.library.rename": Method(hub.library_rename, "rename a picture (`name`, `to`) and every use"),
    "bot.library.delete": Method(hub.library_delete, "delete a picture (`name`)"),
    "bot.library.undelete": Method(hub.library_undelete, "put back the picture or action deleted last"),
    "bot.actions": Method(_actions, "the bot's actions: steps, sections and which actions use each"),
    "bot.action.read": Method(_action_read, "an action's sections and steps, each with its line (`name`)"),
    "bot.action.save": Method(_action_save, "write an action from its `sections` (`name`); its lines come back new"),
    "bot.action.play": Method(
        hub.action_play,
        "play an action (`name`) in the service; `stepping` stops at each line; refused (input_bot_running) while an "
        "input bot runs, unless `replace`",
    ),
    "bot.action.stop": Method(_action_stop, "stop the action playing"),
    "bot.action.resume": Method(_action_resume, "go on from a breakpoint or a step"),
    "bot.action.step": Method(_action_step, "run one line of the action playing, then stop again"),
    "bot.action.breakpoints": Method(_action_breakpoints, "set an action's breakpoints (`name`, `lines`)"),
    "bot.action.rename": Method(_action_rename, "rename an action (`name`, `to`) and every call to it"),
    "bot.action.delete": Method(_action_delete, "delete an action (`name`) and its tape"),
    "bot.days": Method(hub.results_days, "the days the bot has run, newest first"),
    "bot.day": Method(hub.results_day, "one day's results (`day`)"),
}


def find_bot(name_or_path: str) -> Path:
    """The folder of the bot called this (its name or its folder's name), or at this path."""
    wanted = str(name_or_path)
    for folder in hub.project_folders():
        if wanted in (folder.name, str(folder)):
            return folder
        if Path(wanted).expanduser().resolve() == folder.resolve():
            return folder
    for bot in hub.projects_list({}):
        if bot.get("name") == wanted:
            return Path(bot["path"])
    raise ValueError(f"no bot called {wanted}: see darbit bots")


def call(name: str, params: dict) -> object:
    """Run a method; ValueError for an unknown one, a missing bot or a refused request."""
    method = METHODS.get(name)
    if method is None:
        raise ValueError(f"no method called {name}")
    given = dict(params)
    if method.one_bot:
        bot = given.pop("bot", None) or given.get("path")
        if not bot:
            raise ValueError(f"{name} needs `bot`: a bot's name or path")
        given["path"] = str(find_bot(str(bot)))
    return method.run(given)
