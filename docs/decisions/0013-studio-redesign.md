# 0013 darbit Studio's redesign

Accepted, 2026-10-26.

## Context

The first usable Studio (#131) was put together from the components without following the approved mockup. In use it felt messy:
- two menus, the top pill and the bottom dock, and it wasn't clear which was the main one;
- pages without a clear goal;
- bot pages and tool pages mixed together;
- no motion;
- a Library that only knew images, and a Check button for the whole bot;
- resizing lagged, the window forgot its size, and closing quit the app.

## Decision

The Studio is redesigned one choice at a time, from rendered options. The rounds and the full list of what was chosen are in [docs/ui/redesign/](../ui/redesign/README.md). The main points:

- **Structure:**
  - Tools aren't a separate world; they work on the open bot.
  - A bot dropdown (or a sidebar, as a setting) picks the bot, and a centred bar picks its page: Overview, Results, Library, Settings.
  - Play, Pause, Stop and Edit sit on the right. Edit opens the editing tools.
- **The look:** Glass, from the approved mockup. Blur goes only on panels, never on the whole page.
- **The bot fills its pages from its code.**
  - The Overview is made of blocks, and anyone can rearrange them.
  - Results is a template: a summary sentence, a table of gains and progress (`d.record.gain`, `d.progress`) and a whole-day timeline.
  - Common things are shown as rows, not tiles.
- **Library:**
  - every asset type, in a grid with an inspector and a Screen view;
  - Rename updates the bot's code;
  - Test on screen replaces the bot-wide Check.
- **Capture:**
  - the refined toolbar layout, with a magnifier that follows the mouse;
  - a fully editable box, by mouse and keys;
  - Test for the selected image, searching its region and boxing each match with its score.
- **Recorder:**
  - a hiding pill, with a live steps panel on a key;
  - an action editor built for long actions: one list, sticky sections, settings in place, Peek and Open for calls to other actions, Play with breakpoints.
- **The window:**
  - closing keeps darbit running in the tray (a setting), and the tray menu holds the running bot's controls;
  - size and place are remembered;
  - the run pill shows while a bot runs.

## Consequences

- The Studio from #131 and the run pill from #132 are rebuilt on this design: the shell and window first, then each page.
- New runtime calls for bots: `d.record.gain(name, amount, total=, icon=)` and `d.plan([...])`. Both are optional; without them, the pages show plain defaults.
- Renaming an asset needs a safe code rewrite: preview every line, then change all or none.
- `docs/ui/mockups.html` stays as the first concept; `docs/ui/redesign/` is the reference until Storybook has every new screen.
