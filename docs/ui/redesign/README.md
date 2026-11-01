# Studio redesign rounds

The first usable Studio (v0.3 work, PR 131) was built from components without following the approved mockup, and it felt like a mess: two menus, pages without a clear goal, no motion, bot pages and tool pages mixed. The layout is redesigned one decision at a time, from rendered options.

Each round is an HTML page (with a PNG of it) in this folder. `rounds.css` is their shared look.

## Decided

### Round 1: structure (round-1-structure.html)

- Tools aren't a separate world: you only use them on a bot, so they belong to the open bot.
- One menu for bots, plus a centred bar at the top for the open bot's pages.
- The page goals stand, except Runs (see round 2).

### Round 2: bot pages (round-2-bot-modes.html)

- **No Use and Build modes.** The bot's control group holds Play, Pause, Stop and **Edit**. Edit opens the editing tools: add assets with Capture, record actions, rename, test on screen. "Build" only means making a new bot (Add a bot → New).
- **Bot picker:** a dropdown at the top left (as in the first Studio) or a sidebar. Both are built, and a Studio setting chooses.
- **Runs becomes Results:** what the bot achieved this week, problems grouped by cause with a fix (Retake, Show me where), then the timeline of a chosen day. The raw log stays one click away.
- **Storage line:**
  - **The Studio's, on this PC:** theme, keys, hiding on Run, tray, window size and tool behaviour (snap, zoom, recorder delays), kept in `%APPDATA%\darbit`. Installed bots and the cache go in `%LOCALAPPDATA%\darbit`.
  - **The bot's, in its folder:** `darbit.toml`, `settings.toml` and `config.toml`, assets, actions, `guide.toml`, and `.darbit\` for runs, logs and state.
  - **Tools** write only into the open bot's folder.

### Round 3: the look (round-3-look.html)

- **Glass**, the approved mockup's look: see-through panels over a soft colour wash (later the bot's blurred last screenshot). Blur goes only on panels, never on the whole page, so resizing stays smooth.
- **Bot controls**, at the top right: Play, Pause, Stop, then Edit.
- **Motion:** short slides and fades for the run pill and page changes. It answers "there are no animations"; it's shown again on each page in the next round.

### Round 4: the Library (round-4-library.html, round-4b-library.html)

- **Layout:** a grid grouped by screen, with an inspector on the right. Filters cover every type (images, regions, points, actions), plus Missing and Weak.
- **Cards:**
  - a thumbnail, with a chip for its search region;
  - a score meter, with a tick at the similarity it needs;
  - how often it's used;
  - a warning when it's weak.
- **Selection:** the card lifts and glows and gets a check mark; the other cards fade.
- **Inspector:**
  - the asset on its screen (the last screenshot), glowing inside its search region;
  - score, needed similarity and search time, plus a history of its last runs;
  - Test on screen, Retake, Rename and Search region;
  - where it's used, as code lines.
- **Screen view:** a Grid / Screen switch shows the whole screen with every asset in place and a strip of cards below. With Edit on, a box can be dragged, and Capture here takes a new asset from the screenshot.
- **Edit** is a switch. Without it, the Library is browse-and-test only.
- **Rename** previews every line it changes, then changes all of them or none.

### Round 5: Results and Settings (round-5*.html)

- **Results** (5d; it can be polished later):
  - **Day list:** the date, the lead gain and how long it ran, with a red dot on a day with a problem.
  - **The chosen day:**
    - a plain sentence summary;
    - one problem line, shown only when there is one, with its fix;
    - a table of gains and progress (today, the week as small bars, total);
    - a whole-day timeline that zooms (− / +, Ctrl+wheel) and drags (the view or a minimap).
- **Results is a template the bot fills from its code:**
  - `d.record.gain(name, amount, total=, icon=)` adds a gain row;
  - `d.progress(label, done, total)` adds a progress row;
  - timeline lanes are the top-level steps.

  There's no config table. Common things are shown as rows, not tiles, so nothing gets cramped.
- **Settings:** S1. Sections on the left, one form on the right with a dot on changed values, and a save bar that slides up.
- **Overview** is a template too, filled from the bot's code the same way.

### Round 6: Overview, Studio settings, tray (round-6-overview-studio.html)

- **Overview:** configurable, not one fixed layout. It's built from blocks: Now, Today's round, Next up, Progress, Gains, Needs you, log tail. O1 is the default arrangement. The author sets the default in code, and anyone using the bot can rearrange, resize or hide blocks in a Customize mode (saved on that PC). The blocks are filled from the bot's code (`d.step`, `d.next`, `d.progress`, `d.record.gain`, and the new `d.plan` for the round's order).
- **No live screen in the Studio:** the Studio would cover the game. That's an idea for a second monitor later.
- **Studio settings:**
  - S1 layout, opened from ⚙ beside the bot picker or from the tray.
  - Sections: Look, Window, While a bot runs, Keys, Tools, Folders, About & updates.
- **Window:**
  - ✕ keeps the Studio running in the tray by default (Quit is the other choice).
  - Size and place are remembered.
  - Start with Windows is optional.
  - The bot picker is a dropdown or a sidebar.
  - Smooth effects can be turned off.
- **Tray:**
  - darbit's icon gets a dot while a bot runs.
  - Double-click opens the Studio.
  - Right-click: Open, the running bot's Pause, Stop and Show the pill, Studio settings, Quit.

### Round 7: Capture (round-7-capture.html, round-7b-capture.html)

- **Layout:** K1, refined. It runs over the frozen game, dimmed outside the box, with a bottom toolbar and the guide card in a corner. Readouts sit on the box. It saves into the open bot.
- **Two ways in:**
  - **Setup** (a bot someone else made): the guide fills in the name, type and region, and shows how the target looked for the author.
  - **Edit:** add any type (image, region, point) and name it yourself.
- **Magnifier:** a rounded square that follows the mouse without lag (transform, once per frame). It shows a 4× zoom with a pixel grid and the position and colour under it, and it flips side near edges.
- **The selected box:**
  - drag to move, 8 handles to resize, the wheel to scale around the centre;
  - arrows to nudge (Shift for 10 px), Ctrl+arrows to resize;
  - drag the click point, C to centre it, Ctrl+Z to undo;
  - Alt turns off snapping; hold ? for every key.
- **Test** (the old Check):
  - only for the selected image; its button glows while there's something to test;
  - it searches the image's own region, with a sweep;
  - each match gets an animated bracket box with its score, and matches under the similarity line fade;
  - the slider moves the line.
- It can get fancier later.

### Round 8: the Recorder and the action editor (round-8*.html)

- **While recording:** a pill at the top (RA) that hides like the run pill and shows the time, the action's name, step and check counts, Pause, Add check and Stop. Pausing drops the check menu: picture, colour at a point, area changes, wait (text later). A key toggles the live steps panel (RB), which lists each step as it's caught, can delete the last one, and docks to any edge.
- **The action editor** (8d), under Library › Actions:
  - one wide step list, built for long actions;
  - section headers that stick and fold, each with its colour and a progress bar while playing, plus a Jump to menu and search;
  - steps that read like what they do: keycaps, target thumbnails with scores, wait bars;
  - a step's settings, including the screen when it was recorded, unfold in place;
  - ＋ between rows to insert, a ⋮⋮ grip to reorder by dragging, and Shift/Ctrl multi-select with bulk edits in the header;
  - loops as indented blocks;
  - calls to other actions as a pink chip with Peek (read-only, in place) and Open (with a breadcrumb back); the header shows "used by";
  - Play walks a glowing playhead through the steps, and breakpoints stop it;
  - no timeline, outline column or inspector column.
- Actions are saved as plain Python in the bot's `actions/` folder (`with d.step(...)` sections), so they also open in VS Code. Play calls the function and follows it with a line trace (runs/player.py).

### Round 9: the Qt Studio, simplified (round-9-qt-studio.html)

- **One place for each control.** darbit's own settings live in the bot menu (or the sidebar's footer), not in a second ⚙;
  the bot's are its Settings page. The run control changes shape (Play while stopped; Pause and Stop while running)
  instead of showing buttons that can't be used. Customize and the Library's stacked rows are gone: the Library has
  one toolbar.
- **Bots:** a menu in the top bar by default; a sidebar is a darbit setting, and it folds to the bots' squares on a
  narrow window. New bot is one sheet: from the template, from a git link, or a folder already on the PC.
- **Bots that run other bots:** an idea, not built. It may become a general way to control bots from bots.
- **Library:** one grid of every asset with its whole name, not grouped by the first part of the name by default.
  Search, kind, Missing and Weak filter it; it sorts by name, weakest first or most used, and groups by name or kind
  only when asked. The chosen card opens an inspector beside the grid: its numbers, last scores, Retake, Rename,
  Delete and where it's used.
- **Motion:** pages slide in, cards rise in turn, the page bar's highlight glides, the inspector and the save bar
  slide, the progress ring sweeps. Only opacity and position are animated, and nothing moves while the Studio is idle
  (0% of a core, measured). Smooth effects off makes everything show at once.

### Round 10: Capture and the recorder, one family

- **Separate tools, one family.** Capture works on a frozen screen and takes over the mouse; the recorder must stay
  out of the way while the game is played live, so they stay two tools. They share the pill (the state, a few
  controls, the main action last in the accent), the chips and the motion.
- **They meet at checks:** paused on the recorder, "Wait for a picture" opens Capture on that moment; the saved picture
  becomes the check, and the recorder comes back.
- **Capture:** the toolbar is the pill (name, Image / Area / Point, Test, Save), with a magnifier (4×, place and
  colour) and, after Test, a similarity slider that fades the matches under it.
- **Recorder:** a pill at the top of the screen with the time, steps and checks; Checkpoint, Pause (and the check
  menu while paused), Done and ✕; ≡ unfolds the steps as they're caught.

### Round 11: Capture, picture, area and point together (round-11-capture.html)

- **A, layers on the shot.** One target is a picture, the area it's searched in and where to click it, made together
  with no modes: drag or click for the picture, Shift+drag for its area, Ctrl+click for the point. The pill's three
  chips show what the target has; a click on one works on that part, a right-click drops it. Tab goes to the next
  part.
- **The pill moves to the top** and slides away 3 s after the mouse leaves it, like the recorder's and the run pill,
  so what's under it can be boxed; the top edge brings it back.
- **Undo and redo** (Ctrl+Z, Ctrl+Y) for every change; a burst of arrow presses is one step.
- **Readouts** on each part (picture size, area with "picture inside ✓" or "outside ⚠", the click's offset from the
  picture's centre); click one to type exact numbers.
- **A retake keeps** the target's saved area and point, and C held shows the saved picture over the new one.
- **The magnifier** shows the shot's own pixels with the parts on them, Ctrl+wheel zooms it (2× to 24×), Z pins it.
- **Test** searches the picture's own area and says whether it's found once, more or not at all.
- Not chosen: B (three steps in order) and C (a tool rail and a card of numbers).

## Also to fix (from the first Studio)

- Resizing the window lags.
- Window position and size aren't remembered.
- Closing should collapse the Studio to the run pill and a tray icon, not quit.
- Animations are missing.
- Capture still uses the old layout.
- The recorder doesn't exist yet.
- Library:
  - It covers every asset type, not only images.
  - Renaming an asset also updates the bot's code.
  - Check moves out of the bot menu: it becomes a Capture feature that tests one selected asset and highlights it on screen.
