# The service

`darbit serve` runs darbit's service: it starts, pauses and stops bots, whether darbit Studio is open or not. The CLI and the Studio are clients of it.

```bash
darbit bots                    # every bot it knows (starts the service in the background if it isn't running)
darbit bots --add ../my-bot    # add a project folder
darbit start ad-bot            # by name, or by folder
darbit pause ad-bot            # pause; again to go on
darbit stop ad-bot             # it lets go of every key; ended if it doesn't stop within 10 s
darbit status ad-bot
darbit serve                   # run it in this terminal instead; Ctrl+C stops it
darbit serve --stop            # stop the one running in the background
```

Stopping the service leaves its bots running; the next one takes them over.

## Talking to it

The service listens on 127.0.0.1 only. Its port and a token are in `service.json` in darbit's data folder (`%LOCALAPPDATA%\darbit` on Windows), readable only by the user. Messages are one JSON object per line (`service/protocol.py`):

```json
{"type": "hello", "token": "...", "client": "my tool", "version": 1}
{"type": "request", "id": 1, "method": "bot.start", "params": {"bot": "ad-bot"}}
{"type": "reply", "id": 1, "result": {"status": "running"}}
{"type": "event", "topic": "project.status", "data": {"path": "...", "status": "running"}}
```

The first message is `hello` with the token; every request gets a reply with its id, with `result` or `error`; events come as things happen. From Python:

```python
from darbit.service.client import Client, ensure_running

ensure_running()
with Client("my tool") as service:
    service.on_event(print)
    service.call("bot.start", bot="ad-bot")
```

`service.ping` lists every method; `service/methods.py` says what each does.
