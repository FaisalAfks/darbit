# 0014 Recorded input is a tape

Accepted, 2026-10-28.

## Context

The recorder first wrote one Python line per step (decision 0010): a press, a click, a wait, and later `d.move_by` for mouse movement. Played back, the mouse ended up far from where it went while recording. Two facts explain it:

- **Windows accelerates the cursor by packet size.** With "Enhance pointer precision" on, 200 counts sent as 200 packets of 1 moved the cursor 169 px; as 10 packets of 20, 482 px; as 1 packet, 775 px. Steps that bundle movement change the packet sizes, so a free cursor overshoots.
- **A game reads the mouse in one of two ways.** With a free cursor it reads where the cursor is. While it holds the cursor (Roblox's shift lock, a right-drag camera) it reads the raw counts. Exact playback has to give the game whichever one it was reading.

Steps run one after another, so keys, the wheel and movement also couldn't overlap the way they did.

## Decision

A recording is saved as a tape, `actions/<name>.tape.json`, next to its action. The action plays it in parts with `d.replay(__file__, start, end)`; checks added while recording split it into parts.

- **What's kept:** every mouse packet with its counts, where the cursor went and whether it was showing; every key and mouse button going down and up; the wheel, both ways. Times are seconds from the start.
- **Held or free**, judged from the recording in 30 ms buckets: a hidden cursor, or one that snaps back against the movement, or one that goes less than a quarter as far as the mouse moved, is held by the game. A cursor pushed against the edge of the screen is free.
- **Playing:** one clock for every event, sleeping until just before each one and waiting the last 1.5 ms in a tight loop. A held packet sends the same counts; a free one puts the cursor where it went, so Windows' mouse settings don't matter. Clicks put the cursor in place first. If an event goes out more than 8 ms late (the game or Windows took a moment, Python was busy), the rest of the tape moves later with it instead of rushing to catch up, so waits and how long keys are held stay as recorded. A pause from the Studio moves the rest later by the pause, and presses again what the tape was holding, since pausing let go of it.
- **Places follow the game window** (`settings.window`): the window's client area is kept with the tape, and places are scaled to where the window is now.
- **Checkpoints** (Ctrl+Alt+K, or the bar's ⚑) split a recording into parts, and each part is saved as its own action with its own tape (`Dim_Run_1`, `Dim_Run_2`…), its times starting from 0. The recorded action (`Dim_Run`) calls them in order. Re-record replaces one action and its tape, so one part can be done again while the rest stay; Rename updates the files and every caller. A key held across a checkpoint stays down into the next part.
- **Pausing** lets go of held keys on the tape and leaves the paused time out of it.
- **The editor** shows each part as a block: its time range, counts, a mini path of the cursor and marks for keys, clicks and the wheel. A part can be trimmed and split, and checks go between parts.

Recorded actions stay `@d.flow(timed=True)`. The steps the recorder bar shows while recording (presses, clicks, scrolls, checks) are only for the bar.

## Consequences

- Movement plays back exactly: in tests on the desktop, a free cursor ended on the recorded pixel, and a game holding the cursor received the recorded counts exactly.
- Recorded movement isn't Python lines any more. It's edited as parts of a tape, while hand-written actions keep using `d.click`, `d.move_by`, `d.mouse_down` and the rest.
- Tapes are big, about 2 MB a minute for a 1000 Hz mouse, and they're data, not code to review.
- Playing keeps one CPU core busy for the last moment before each event.
- Python runs one thread at a time and by default switches every 5 ms; with the Studio's other threads busy, the raw input thread fell behind and mouse counts were lost. While recording or playing, threads switch every 0.5 ms (`platform/switching.py`). When the listener still gets to an input late, its time comes from the message's own time (GetMessageTime) instead of the moment it was read, so a run of inputs read at once keeps the waits between them (`platform/stamps.py`). Each tape's `notes` say how many inputs came in late, the latest, and how many Windows no longer had (lost counts), to tell a bad recording from a bad replay. Roblox was checked to take replayed counts 1:1 at any speed.
- A game that reads raw counts while showing a free cursor would get the cursor placed instead of the counts. That's rare; it would need a switch on the action.
- At a very slow Windows pointer speed (a free cursor moving less than a quarter of the counts), a free cursor would be taken for a held one.

**Update (rebuild, milestone 3):** recording runs in the input worker (`python -m darbit.worker`), a process of its own
that darbit Studio starts and talks to over its stdin and stdout, so the Studio's window and threads can't delay an
input. Bots play their tapes in their own process, which runs nothing else.
