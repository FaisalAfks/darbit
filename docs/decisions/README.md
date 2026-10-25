# Decisions

Architecture decision records: one short file per decision, with its context, the decision and what follows from it. A decision is changed by a new record that replaces the old one, never by editing history.

| # | Decision | Date |
|---|---|---|
| [0001](0001-tagged-releases-dev-and-live.md) | Bots run tagged releases; development happens in a separate clone | 2026-10-25 |
| [0002](0002-monorepo.md) | One darbit monorepo: library, web UI, VS Code extension | 2026-10-25 |
| [0003](0003-uv.md) | uv for environments, locking and installing | 2026-10-25 |
| [0004](0004-agents-md-and-agents-folder.md) | `AGENTS.md` and `.agents/` for AI tools, no tool-specific files | 2026-10-25 |
| [0005](0005-ui-process.md) | One more HTML concept round, then Storybook with the real components | 2026-10-25 |
| [0006](0006-data-folders.md) | Where darbit keeps its files: AppData and a project's `.darbit/` | 2026-10-25 |
| [0007](0007-studio-flows-and-actions.md) | The hub becomes darbit Studio: flows, actions, two-way with Python | 2026-10-25 |
| [0008](0008-readable-python.md) | Plain, readable Python | 2026-10-25 |
| [0009](0009-public-darbit.md) | darbit public from v0.2.0, ad-bot private | 2026-10-25 |

The full plan these came from: [plan-2026-10-25.md](../plan-2026-10-25.md).
