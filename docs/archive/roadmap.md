# darbit roadmap

Each version is a milestone on the project board. A milestone closes when its "done when" has been shown working. The design behind each part is in [design.md](design.md); instructions for every task are in [tasks/](tasks/README.md).

| Version | Content | Done when |
|---|---|---|
| **v0.1** core | finding and waiting, mouse and keyboard, apps, settings, the stop hotkey, logs, the capture tool | `v0.1.0` is tagged and released |
| **v0.2** runtime | observers and interrupts, the state store, one capture per check, the run report, targets that follow the window and rescale, `darbit check` | a bot rejoins on a Disconnected message through an observer, and `darbit check` reports its whole library |
| **v0.3** UI system | design tokens and components, the local server, the keymap and themes, the capture tool rebuilt on the web UI (click to select, snapping, magnifier, readouts, linked regions, editing), highlight, setup guides, a faster screen capture, the freeze-overlay test | a capture session works on the web UI and looks like the mockups |
| **v0.4** runs and flows | the flow format and its schema (recorded steps, checks, loops, functions), the recorder with checks added while recording, the player, the live run panel | a dimension run is recorded, edited live and played by a bot |
| **v0.5** projects | `darbit.toml`, the settings schema and its generated form, `darbit new`, `install` and `run`, darbit Studio (install wizard, tools launcher), the flow editor, flow ↔ Python, custom actions | a bot is installed from its git link, set up in the hub and run |
| **v0.6** IDE extension | `darbit-vscode`: previews, go to target, errors, capture and record commands, running with the live panel, run-file editor, library view | a bot is written, captured, recorded and run from VS Code |
| **v0.7** text and masks | targets read with OCR, masks | a bot reads a number from the screen with a text target |
| **v1.0** stable | a frozen public API, the docs site, a Windows installer, a benchmark baseline | a new user installs darbit and builds a first bot from the docs alone |
| after v1 | MCP, macOS and Linux, a registry of bots | |
