# 0015 Rebuild around a fast, swappable core

Accepted, 2026-10-30.

## Context

A review of darbit v0.4 and ad-bot found:

- Windows calls spread through about ten modules, with no interface between them and the rest.
- Pictures matched at their exact pixel size over the whole screen, and ad-bot's positions and regions fixed for a 2560 x 1600 screen at 150%.
- The Studio (Svelte in pywebview, behind a local web server) built before the engine was solid: about 700 MB, real-time input sharing a process with the UI, workarounds for thread switching and transparency.
- Two capture tools, placeholder modules for unfinished tasks, and style rules (0008) that made code longer without making it clearer.

## Decision

darbit is rebuilt by the [rebuild plan](../plan-rebuild.md):

- **A library first:** the core API on Region and Pattern, the SikuliX way; the Studio is a client over it.
- **Swappable interfaces** for screen, input, windows, listener, hotkeys, matcher and reader, Windows first.
- **Detection changes are options, never forced.** Full-colour template matching at the picture's own size stays the default; screen pixels stay the default, window space is an option to measure.
- **Processes:** the bot, a service that runs bots, an input worker for recording and playback, and the Studio, over a local socket with typed JSON.
- **The Studio in PySide6 with QML.**
- **Code style** relaxed: simple comprehensions and key lambdas are fine ([code.md](../style/code.md)); no stub files for future work.
- **The repo:** `main` is rebuilt; v0.x stays in the `v0.4.0` tag and the `maint/0.x` branch, and bots keep their pinned release until they're ported.

## Consequences

- Replaces [0005](0005-ui-process.md) (the HTML and Storybook UI process) and [0008](0008-readable-python.md) (the strict style rules), and the web stack parts of [0002](0002-monorepo.md) and [0013](0013-studio-redesign.md). 0013's page designs stay the reference for the new Studio.
- `main` has no working Studio until milestone 4; the current Studio runs from a `v0.4.0` checkout meanwhile.
- The roadmap, the design page, the 2026-10-25 plan and the task pages move to [docs/archive](../archive/README.md).
