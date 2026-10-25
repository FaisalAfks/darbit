# AGENTS.md

How to work in this repo. Read by every coding tool (Claude Code, Antigravity, Gemini CLI, Codex, Cursor, Copilot) and by people. Longer guides live in `docs/`; this file points to them.

## What this is

darbit: simple GUI automation for Windows, in Python, an improvement on SikuliX. Find images on screen, click, type, wait. It also becomes **darbit Studio**, an app that installs and runs bots, captures and highlights targets, and records and edits flows. A monorepo:

| Path | What |
|---|---|
| `packages/darbit/` | the Python package (`src/darbit/`) and its tests |
| `packages/ui/` | the web UI (Svelte), built into the Python package |
| `packages/vscode/` | the VS Code extension (later) |
| `docs/` | the docs site: guides, architecture, style, decisions, roadmap, task pages |
| `examples/` | the smallest working bot |
| `scripts/` | dev helpers (`setup-dev.ps1`, `render_mockups.py`) |
| `.agents/skills/` | step-by-step how-tos for common jobs (release, new task, review, mockups) |

Start with [docs/architecture/index.md](docs/architecture/index.md), then [docs/decisions/](docs/decisions/README.md) for why things are the way they are, and [docs/tasks/](docs/tasks/README.md) for what to build next.

## Commands

```bash
pwsh scripts/setup-dev.ps1   # once per clone: uv sync, and the .claude/skills link
uv run pytest                # tests (never touch the real mouse or keyboard)
uv run ruff check .          # lint
uv run ruff format .         # format
uv run --group docs mkdocs serve   # the docs site at http://127.0.0.1:8000
python scripts/render_mockups.py   # mockup images into docs/ui/images/
```

## Rules

**Git and GitHub**
- Never commit or push to `main`. One branch per task (`feature/<issue>-<name>`, `fix/<issue>-<name>`, `docs/…`, `refactor/…`), and a PR into `main` that says `Closes #<issue>`.
- Never merge. The owner merges; ask first.
- Every change has an issue on the "Anime Dimensions" project board, in its milestone.
- Releases: SemVer tags `vX.Y.Z` on `main`, with a GitHub release and short notes (`.agents/skills/release`).

**Writing** (commits, PRs, issues, releases, changelog, docs, comments)
- In the owner's voice: plain, minimal, simple.
- Never "I", "we" or "the user"; nothing about who asked for what.
- Never mention AI, assistants or agents in anything public. No `Co-Authored-By` or "Generated with" lines.
- Describe what changed and why it matters to the code. Details: [docs/style/writing.md](docs/style/writing.md).

**Code**: see [docs/style/code.md](docs/style/code.md).
- Plain, readable Python (decision 0008): no walrus, no lambdas beyond a one-word key, no tricky comprehensions, no `getattr` dispatch, no `from __future__ import annotations`. Small functions with verb names; small dataclasses instead of tuples.
- Every module starts with a 2–4 line summary. Docstrings are one line, plus arguments when they're not obvious; comments say why.
- Layers only import downward: `core` ← `platform` ← `runtime` ← `tools`/`capture`/`runs`/`project` ← `server` ← `desktop`.
- The public API stays SikuliX-simple: `d.click("Play")`. Not finding something returns `None` or `False`; it never raises.
- `import darbit` works without the `app` extra: import Studio-only packages inside functions.
- Placeholder files (`TODO(Txx)`) belong to their task in `docs/tasks/`; fill them in, don't move them.
- Keep files' line endings (LF in the repo, see `.gitattributes`).

**Docs**
- Every PR updates `CHANGELOG.md` and the docs it touches.
- A decision that changes how things are done gets a record in `docs/decisions/`.
- UI follows [docs/style/ui/design-system.md](docs/style/ui/design-system.md) and the keys in `packages/darbit/src/darbit/keymap.toml`.

**Safety**
- Tests use fakes and saved screenshots. Live input (mouse, keys, the capture tool on screen) only when the owner says so.
- Never commit secrets or private game data: a private server link lives only in an environment variable.

**Asking**
- Ask questions as multiple choice whenever the answer is a choice. Keep messages short, one topic at a time.
