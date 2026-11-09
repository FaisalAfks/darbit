# The service

`darbit serve` runs darbit's service: it starts, pauses and stops bots, whether darbit Studio is open or not. The CLI and the Studio are clients of it.

Started from the Studio or the CLI, the service runs on its own: closing the terminal, editor or Studio that started it leaves it and its bots running. On Windows it leaves the job of the program that started it (a job ends every process in it when it closes) wherever that job allows; one that doesn't keeps it in, and it ends with that program.

```bash
darbit bots                    # every bot it knows (starts the service in the background if it isn't running)
darbit bots --add ../my-bot    # add a project folder
darbit start my-bot            # by name, or by folder
darbit start my-bot --replace  # stop the bot using the mouse and keys first
darbit start my-bot --only "Daily quest" --step "claim it"   # one mode, or one step of it, then it ends
darbit pause my-bot            # pause; again to go on
darbit stop my-bot             # it lets go of every key; ended if it doesn't stop within 10 s
darbit status my-bot
darbit history my-bot          # what it did on its latest day: gains, steps, problems (or a DAY; --days lists them)
darbit serve                   # run it in this terminal instead; Ctrl+C stops it
darbit serve --stop            # stop the one running in the background
```

Stopping the service leaves its bots running; the next one takes them over.

## One bot that sends input at a time

Bots on one desktop share one mouse and keyboard: two that both click break each other. The service runs any
number of bots, but only one that sends input (decision 0020). A bot that never does says so in its darbit.toml:

```toml
[run]
input = false     # true by default
```

Starting a bot that sends input while another one runs (or is paused) is refused, naming the running one:

```text
$ darbit start other-bot
my-bot is running and uses the mouse and keys: one such bot runs at a time.
darbit start other-bot --replace stops it and starts other-bot.
```

`--replace` (`replace: true` on `bot.start`) stops the running one cleanly, as Stop does, then starts the new one.
A bot with `input = false` starts alongside anything, and anything starts alongside it. The rule sits in the
service's start, so every way of starting a bot keeps it: the Studio, the CLI, and the service itself starting a
failed bot again (`[run] restart`): a restart that would collide is told as a failure, with the reason.

An action played from the Studio (Play, Step through, breakpoints; `bot.action.play`) clicks and types from the
service, so it counts too: it's refused while a bot that sends input runs or is paused, its own bot included, and
`replace: true` on `bot.action.play` stops that bot first. Starting a bot that sends input while an action plays (or
waits at a breakpoint) is refused the same way, and `replace` stops the action. Recording an action is refused while
a bot that sends input runs or is paused, or an action plays: stop it first. Starting a bot that sends input, or playing an action,
during a recording is refused, and `replace` doesn't change that: finish or cancel the recording first.

A bot started without the service (`uv run my-bot`, `darbit run`) can't be refused: the service doesn't know about
it, and won't stop a bot started after it. As it starts, such a bot asks the service whether a bot that sends input
is running and warns (in its log and on the terminal) when one is. Start bots through the service to have them kept
apart.

## One mode or one step

`only` on `bot.start` (`{"mode": "Daily quest"}`, or with `"step"`) runs one of the modes or steps the bot's
darbit.toml declares instead of its round (decision 0022, [Bot projects](projects.md#modes-and-steps)). One it
doesn't declare is refused before anything is stopped. The bot gets it as `DARBIT_ONLY`; `bots.list` and
`bot.status` say what a running bot was started for (`only`) and list its `modes`. A run of one mode or step that
fails isn't started again by `[run] restart`. Everything else is as for a round: one bot that sends input at a time,
Stop, the log and the results.

## Notifications

The service tells a phone when a bot fails, when a running bot's report has been quiet too long (it may be stuck),
and sends a summary of each bot's day. Set the channels in `notify.toml` in darbit's settings folder
(`%APPDATA%\darbit` on Windows), any of:

```toml
[ntfy]
topic = "my-darbit-1234"          # the ntfy app, subscribed to this topic; server = "..." for your own
[discord]
webhook = "https://discord.com/api/webhooks/..."
[telegram]
token = "123:ABC"
chat = "123456"

[when]                            # the defaults
failed = true
ended = false                     # a bot stopping on its own or from the Studio
stuck_minutes = 15                # 0 is off
failing = true                    # an image the last failures all came down to: it may have stopped matching
summary = "23:30"                 # "" is off
```

`darbit notify` sends a test message to each channel and says which ones it reached. The service reads the file
when it starts.

## Run history

Each bot's run report lines are copied into `.darbit/history.db` (SQLite) as the bot writes them, and again whenever
history is asked for, so a bot on any darbit version has one. The Results page and `darbit history` query it
instead of reading a day's report again. The tables are `events` (`day`, `time`, `kind`, and the report `line` as
written), `reports` (how far each report has been copied) and `forgotten` (the day history was last dropped
before); `server/history.py` has the queries.

Image looks (`exists`, `wait`, `vanish`, `find`), about nine lines in ten of a report, are left out of history. The
Results page's problems need them, and read them from the day's report, which keeps every line. A history from an
older darbit loses its looks once, a day at a time, and the file is then given back with `VACUUM` (left for the
next tidy if another connection is busy). History is kept for the bot's `keep_days`
([decision 0021](../decisions/0021-keeping-history-small.md)).

## Talking to it

The service listens on 127.0.0.1 only. Its port and a token are in `service.json` in darbit's data folder (`%LOCALAPPDATA%\darbit` on Windows), readable only by the user. Messages are one JSON object per line (`service/protocol.py`):

```json
{"type": "hello", "token": "...", "client": "my tool", "version": 1}
{"type": "request", "id": 1, "method": "bot.start", "params": {"bot": "my-bot"}}
{"type": "reply", "id": 1, "result": {"status": "running"}}
{"type": "reply", "id": 2, "error": "my-bot is running and uses the mouse and keys too: ...", "code": "input_bot_running", "detail": {"running": [{"name": "my-bot", "path": "...", "status": "running", "input": true}]}}
{"type": "event", "topic": "project.status", "data": {"path": "...", "status": "running"}}
```

The first message is `hello` with the token; every request gets a reply with its id, with `result` or `error`; events come as things happen. A refusal a client can act on also has a `code` and a `detail`; the only one so far is `input_bot_running`, whose `detail.running` lists the bots in the way, each as `bots.list` shows it (an action playing or being recorded is its bot's entry with `status` `"playing"` or `"recording"` and `action`, its name; a recording isn't stopped by `replace`). A client asks the person, then sends `bot.start` (or `bot.action.play`) again with `replace: true`. Fields a client doesn't know are skipped (from the release after 1.0.0-alpha.6; an older client can't read a refusal with a `code`). `bots.list` and `bot.status` say each bot's `input`; `bots.running` lists only the running and paused ones; `inputs.running` lists everything sending input now, as a refusal's `detail.running` would: input bots running or paused, the action playing and the recording on. From Python:

```python
from darbit.service.client import Client, ServiceError, ensure_running

ensure_running()
with Client("my tool") as service:
    service.on_event(print)
    try:
        service.call("bot.start", bot="my-bot")
    except ServiceError as error:
        if error.code == "input_bot_running":
            print("in the way:", [bot["name"] for bot in error.detail["running"]])
```

`service.ping` lists every method; `service/methods.py` says what each does.
