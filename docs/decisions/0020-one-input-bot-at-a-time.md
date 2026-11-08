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

## Consequences

- Replies can carry `code` and `detail` beside `error`; they're left out when unset, so a reply without them reads the
  same as before. From this release on the protocol's decoder skips fields it doesn't know; a client from
  1.0.0-alpha.6 or before can't read a refusal that has them and waits until its request times out. The Studio and
  the CLI come with the service, so only a mix of versions meets this.
- Each `[run]` key is checked, so a bot that sets `input` needs a darbit that knows it: an older one refuses the
  darbit.toml.
- Playing an action from the service (`bot.action.play`) sends input from the service's own process and isn't covered
  yet (#428).
- The Studio's side, asking before replacing and listing every running bot in the run pill and the tray, is #427 and
  #424.
