# AGENTS.md

How to work in this repo. Read by every coding tool (Claude Code, Antigravity, Gemini CLI, Codex, Cursor, Copilot) and by people. Longer guides live in `docs/`; this file points to them.

## What this is

darbit: a Python library for automating any app from what's on its screen, an improvement on SikuliX: find images on screen, click, type, wait. **darbit Studio** is its companion app: it runs bots, captures and highlights targets, and records and edits actions. darbit is being rebuilt by the [rebuild plan](docs/plan-rebuild.md) ([decision 0015](docs/decisions/0015-rebuild.md)); v0.x lives in the `v0.4.0` tag and the `maint/0.x` branch. A monorepo:

| Path | What |
|---|---|
| `packages/darbit/` | the Python package (`src/darbit/`) and its tests |
| `packages/ui/` | the v0.4 web UI (Svelte), to be replaced by the PySide6/QML Studio |
| `packages/vscode/` | the VS Code extension (later) |
| `docs/` | the docs site: the rebuild plan, guides, architecture, style, decisions, the archive |
| `examples/` | the smallest working bot |
| `scripts/` | dev helpers (`setup-dev.ps1`, `render_mockups.py`) |
| `.agents/skills/` | step-by-step how-tos for common jobs (release, new task, review, mockups) |

Start with [docs/plan-rebuild.md](docs/plan-rebuild.md) for what darbit is and what's built next, then [docs/decisions/](docs/decisions/README.md) for why things are the way they are.

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
- Merge a PR once its checks pass.
- Every change has an issue on the "Anime Dimensions" project board, in its milestone.
- Releases: SemVer tags `vX.Y.Z` on `main`, with a GitHub release and short notes (`.agents/skills/release`).

**Writing** (commits, PRs, issues, releases, changelog, docs, comments)
- In the owner's voice: plain, minimal, simple.
- Never "I", "we" or "the user"; nothing about who asked for what.
- Never mention AI, assistants or agents in anything public. No `Co-Authored-By` or "Generated with" lines.
- Describe what changed and why it matters to the code. Details: [docs/style/writing.md](docs/style/writing.md).

**Code**: see [docs/style/code.md](docs/style/code.md).
- Idiomatic, readable Python (decision 0015): small functions with verb names, small dataclasses instead of tuples, simple comprehensions and key lambdas are fine; no clever one-liners, walrus, `getattr` dispatch or `from __future__ import annotations`. Bot code and `examples/` stay the plainest.
- Every detection change (grayscale, a downscaled pass, sizes, OCR, window space) is an option; the default stays as it is.
- Every module starts with a 2–4 line summary. Docstrings are one line, plus arguments when they're not obvious; comments say why.
- System-specific code sits behind the plan's interfaces (screen, input, windows, listener, hotkeys); layers only import downward.
- The public API stays SikuliX-simple: `d.click("Play")`. Not finding something returns `None` or `False`; it never raises.
- `import darbit` works without the `app` extra: import Studio-only packages inside functions.
- No stub files for future work: future work is an issue.
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
