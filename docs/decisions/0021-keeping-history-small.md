# 0021 14 days of reports, logs and history; no image looks in history

Accepted, 2026-11-09.

## Context

A bot that runs all day leaves about 10 MB a day. On a real bot after two weeks (15 days): run reports 66.0 MB,
history.db 95.5 MB, daily logs 4.9 MB. The service already deleted days older than `[run] keep_days` (30 by default,
#209), so nothing had gone yet, and the cutoff went by the PC's date, not the bot's day: a bot whose day starts at
midnight UTC on a PC ahead of UTC could lose its yesterday with a small `keep_days`.

About nine report lines in ten are image looks: of 327,541 history rows, 302,014 were `exists` and 5,280 `wait`
(62.1 MB and 0.9 MB of the 65.4 MB of lines). Their readers:

- **The Results page's problems** (`server/problems.py`, through `results.day`): which images ran out before a
  failed step, the closest they came, whether they were seen earlier that day, and the steps before the failure.
- **The Overview** (problems, the failing image) and **notifications** read today's report file, not history.
- `darbit bench --from-screens` reads `.darbit/screens/`, `tools/report.py` a report file. Nothing else reads looks
  from history.

## Decision

- **`keep_days` is a darbit setting,** `[settings] keep_days` or `d.settings.keep_days`, 14 by default: run reports,
  daily logs and history from before today minus `keep_days` are deleted, so today and the 14 days before it stay.
  Days go by the bot's `day_starts` (`days.first_kept`), and today's and yesterday's are never deleted, whatever it
  says. `[run] keep_days` is still read, for darbit.toml files that have it.
- **Whoever writes a file deletes it.** The bot deletes its own old reports and logs (`runtime/log.py`) when it first
  writes and as each new day starts. The service deletes old history from history.db when it starts, when it starts
  a bot, and every six hours; it also deletes old files, for bots on an older darbit that don't yet.
- **History leaves out image looks** (`exists`, `wait`, `vanish`, `find`): `history.LEFT_OUT`. The report files keep
  every line for their days. Results' problems read the day's report when the day has a failed step (history says
  so), through the Overview's reader that keeps the last three reports read. Without the report, they use what
  history has.
- **A day forgotten stays forgotten:** history notes the day it last forgot before, and a report from before it (one
  a reader held open, so it couldn't be deleted yet) isn't copied in again.
- **An existing history shrinks once:** the service's tidy deletes the looks a day at a time (each its own short
  transaction, on the `(day, kind)` index), then runs `VACUUM` once a quarter of the file is free. `VACUUM` waits 1 s
  at most for other connections and is otherwise left for the next tidy.

## Consequences

- On a copy of the same bot's `.darbit`: history.db 95.5 MB to 4.1 MB (307,294 rows out, 1.3 s with the `VACUUM`);
  the copy had 15 days, so `keep_days` deleted nothing yet; a day later it drops the oldest (2.5 MB of files).
- The Results page shows the same problems; a day's start and end, from its first and last event, can move by under
  a second, and its run time by up to 10 s, now that looks aren't among them. Opening a day is about twice as
  fast.
- A bot that sets `keep_days` in `[settings]` needs a darbit that knows it: an older one refuses the darbit.toml.
