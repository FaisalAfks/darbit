# AGENTS.md

How to work in this repo. Read by every coding tool (Claude Code, Antigravity, Gemini CLI, Codex, Cursor, Copilot) and by people. Longer guides live in `docs/`; this file points to them.

## What this is

darbit: a Python library for automating any app from what's on its screen, an improvement on SikuliX: find images on screen, click, type, wait. **darbit Studio** is its companion app: it runs bots, captures and highlights targets, and records and edits actions. darbit is being rebuilt by the [rebuild plan](docs/plan-rebuild.md) ([decision 0015](docs/decisions/0015-rebuild.md)); v0.x lives in the `v0.4.0` tag and the `maint/0.x` branch. A monorepo:

| Path | What |
|---|---|
| `packages/darbit/` | the Python package (`src/darbit/`) and its tests |
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
- GitHub checks these: pre-commit refuses a commit on `main`, the `pr-rules` check fails a PR without `Closes #<issue>` or a `CHANGELOG.md` line (label `skip-notes` when none is needed), and issues opened from the forms go on the board.
- Merge a PR once its checks pass.
- Every change has an issue on the "Anime Dimensions" project board, in its milestone.
- The board is where open work lives: move an issue to In progress when work starts, and only close it once its PR is merged. A new idea or a problem found in logs becomes an issue, not a note in a doc.
- Releases: SemVer tags `vX.Y.Z` on `main`, with a GitHub release and short notes (`.agents/skills/release`).

**Writing** (commits, PRs, issues, releases, changelog, docs, comments)
- In the owner's voice: plain, minimal, simple.
- Never "I", "we" or "the user"; nothing about who asked for what.
- Never mention AI, assistants or agents in anything public. No `Co-Authored-By` or "Generated with" lines.
- Describe what changed and why it matters to the code. Details: [docs/style/writing.md](docs/style/writing.md).

**darbit and its bots** ([decision 0018](docs/decisions/0018-darbit-and-its-bots.md))
- darbit holds what any bot for any game would use unchanged; a bot holds what only makes sense for its game (its
  screens, modes, timings, rules, names). The test: would a bot for a different game want it as it is?
- No setting, default or wording in darbit shaped around one bot. Examples and placeholders use neutral names.

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

**How work is done**
- Check how a tool, library or system really behaves (its docs, a quick test) before building on it or writing it into a plan; cite it in the decision record.
- Plans are complete and researched before they're shown: they may be approved without every line being read.
- UI choices are made from rendered options (HTML or an image, `.agents/skills/render-mockups`), one decision per round, structure before style, then a multiple-choice question naming them. [docs/ui/mockups.html](docs/ui/mockups.html) is the reference look.
- Modular and finished: extend the shared component or service that exists (FloatingPill, PillWindow, PillButton, Chip, Block, ...) before adding a parallel one, and never half-do a feature. After building, check it looks and behaves like its siblings and nothing in its issue is left out.
- One set of names everywhere (UI, docs, files, code): **Image**, **Region**, **Location**; never picture, area or point.

**Working in parallel**
- Two areas: **Studio** (`packages/darbit/src/darbit/studio/`, its QML, issues labelled `area: studio` or `area: ui`) and **core** (everything else). Each line of work takes issues from its own area.
- Work that runs alongside other work uses its own worktree (`git worktree add ../.worktrees/<branch> -b <branch>`), never the shared clone's working tree; the shared clone stays on `main`.
- A change one area needs from the other becomes an issue for that area. The same goes for bots: a bot asks for a change with an issue here, and gets it through a release (`v1.0.0-alpha.N`, `.agents/skills/release`) and a pin move on its side. darbit never depends on a bot.

**Live testing on a desktop**
- `DARBIT_LIVE=1 uv run pytest packages/darbit/tests/live` runs the live tests here, as CI does; `DARBIT_LIVE_SHOTS` names a folder for their screenshots.
- `DARBIT_HOME` set to a temporary folder keeps scripts and probes away from the real settings, service and bots (the test run sets it).
- Probes that open Qt windows draw off-screen and as tool windows; nothing shows up while a bot plays.
- Start the Studio detached from whatever terminal or tool runs the command (`Win32_Process.Create` through WMI), or it ends, with its service and bot, when that program closes.
- Never lock the screen to test the locked-screen pause: nothing can unlock it remotely.
- Write files the Studio reads with Python: Windows PowerShell's `Set-Content` adds a byte-order mark.

**Safety**
- Tests use fakes and saved screenshots, with `DARBIT_NO_REAL_INPUT=1` (tests/conftest.py): a real click, key, app control or screen grab raises. Live input (mouse, keys, the capture tool on screen) only when the owner says so.
- Never commit secrets or private game data: a private server link lives only in an environment variable.

**Asking**
- Ask questions as multiple choice whenever the answer is a choice. Keep messages short, one topic at a time.
