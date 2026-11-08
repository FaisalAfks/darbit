# 0020 One bot that sends input at a time

Accepted, 2026-11-08.

## Context

The rebuild plan has the service run any number of bots, each on its own window, account or monitor (section 5).
Windows, monitors and accounts can be kept apart; the mouse and keyboard can't. There is one cursor and one keyboard
focus per desktop, and darbit's input (`SendInput`) moves that cursor and types into whatever has focus. Two bots that
both click take the cursor from each other mid-move and type into each other's window, and both fail in ways their
logs don't explain.

Some bots never send input: one that only watches a screen and records what it reads, or one that only sends
notifications. Those can run next to anything.

What the service could see when this was decided: the bots it started itself (its own runs) and the ones an earlier
service started, found through the pid file in each bot's control folder. A bot started some other way (`uv run
my-bot`, `darbit run`, a terminal) has no pid file and doesn't talk to the service.

## Decision

- **darbit stays able to run several bots at once;** by default only one of them sends input.
- **A bot says whether it sends input in its darbit.toml,** `[run] input`, true by default. `input = false` is for a
  bot that never clicks, types or moves the mouse; darbit doesn't check that it keeps its word.
- **The service's start refuses an input bot while another input bot is running or paused.** The reply's `error`
  names the running bot for people; `code` is `input_bot_running` and `detail.running` lists the bots in the way
  (name, path, status, input, as `bots.list` shows them), for a client to ask "stop X and start Y?".
- **`replace: true` on `bot.start`** stops the bots in the way as Stop does (each lets go of every key, and is ended if
  it doesn't stop within 10 s), then starts the new one. A replaced bot ends as stopped, not failed, so its
  `[run] restart` doesn't start it again.
- **The rule sits in the service's start,** under one lock, so two starts at once can't both get through, and every
  way of starting a bot follows it: the Studio, the CLI (`darbit start`, with `--replace`), and the service starting a
  failed bot again. A restart that would collide is told as a failure with the reason, like any refused restart.
  Nothing in the service starts bots on a schedule yet; when it does, it starts them through the same call.
  Notifications never start bots.
- **The service says each bot's `input`** in `bots.list` and `bot.status`, and lists the running and paused bots in
  `bots.running`.
- **A bot started without the service can't be refused.** As it starts (`import darbit`, when its darbit.toml has
  `input = true` and the service didn't start it), it asks the service on a thread of its own whether another input
  bot is running, and warns in its log and on the terminal when one is. It never stops the bot or waits for the
  service. The other way round, the service doesn't see such a bot at all, and starts an input bot next to it.
- **An action played in the service counts as an input bot** (#428). `bot.action.play` (Play, Step through and
  breakpoints in the Studio) clicks and types from the service's own process, so it's refused while any input bot
  runs or is paused, its own bot included (that would be two at once too), and whatever the bot's `[run] input`
  says. The refusal is the same: `code` `input_bot_running`, `detail.running`. `replace: true` stops the bots in the
  way as Stop does, then plays. The other way round, an input bot's start is refused while an action plays, paused at
  a breakpoint or a step included; `detail.running` has the action as its bot's entry with `status` `"playing"` and
  `action` (its name). `replace` stops the action and waits for it to let go of every key (10 s at most) before the
  bot starts. Both go under the start's lock.
- **Recording is refused while an input bot runs or is paused, or an action plays** (#435). The recorder leaves out input that was sent rather
  than typed (Raw Input from `SendInput` has no device, `platform/win32/listener.py`), so a bot's clicks wouldn't
  end up in the action, but the bot would still move the cursor, take the focus and change the screen under the
  person recording, and the recorded places would be wrong. The recorder runs in the Studio's input worker, not the
  service: before it starts, the worker asks the service what sends input now (`inputs.running`: the input bots
  running or paused, the action playing as its bot's entry with `status` `"playing"`, the recording on) and answers
  `record.start` with the same refusal, its error ending "stop it to record ...". There is no replace:
  `record.start`'s `replace` already means Re-record. A service from before `inputs.running` is asked `bots.list`
  instead, which has no actions. No service answering means nothing to refuse.
- **An input bot's start and an action's play are refused during a recording** (#431). The worker writes
  `recording.json` in darbit's data folder (its pid, the bot's folder, the action's name) as a recording starts and
  takes it away as it stops; the service reads it under the start's lock. A file whose worker is gone (it crashed,
  the Studio was ended) counts for nothing, so the start goes ahead. The refusal is the same, with the recording as
  its bot's entry in `detail.running` with `status` `"recording"` and `action`. `replace` doesn't stop a recording:
  only the person recording ends it, so the start is refused even with `replace`, its error saying to finish or
  cancel the recording first. A file rather than a message to the service, so a recording started before the
  service (or before it was restarted) still counts.

## Consequences

- Replies can carry `code` and `detail` beside `error`; they're left out when unset, so a reply without them reads the
  same as before. From this release on the protocol's decoder skips fields it doesn't know; a client from
  1.0.0-alpha.6 or before can't read a refusal that has them and waits until its request times out. The Studio and
  the CLI come with the service, so only a mix of versions meets this.
- Each `[run]` key is checked, so a bot that sets `input` needs a darbit that knows it: an older one refuses the
  darbit.toml.
- The Studio's side, asking before replacing and listing every running bot in the run pill and the tray, is #427 and
  #424.
