# 0004 `AGENTS.md` and `.agents/` for AI tools, no tool-specific files

Accepted, 2026-10-25.

## Context

The repos are worked on with several AI tools: Claude Code, Antigravity and Gemini CLI, Codex, Cursor and Copilot. Instructions were scattered:

- a global `~/.claude/CLAUDE.md`;
- a copy of a prompt saved as `AGENTS.md` outside any repo;
- nothing for the other tools.

What each tool reads, checked on 2026-10-25:

| Tool | Instructions | Skills | Notes |
|---|---|---|---|
| Claude Code | root `AGENTS.md`, when there is no `CLAUDE.md` or `CLAUDE.local.md` | `.claude/skills/` only | `~/.claude/CLAUDE.md` doesn't stop it reading `AGENTS.md` |
| Antigravity | `AGENTS.md`, `.agents/rules/` (older: `.agent/rules/`) | — | rules up to 12,000 characters each |
| Gemini CLI | `GEMINI.md` by default; `AGENTS.md` if set in settings | `.agents/skills/` (takes precedence over `.gemini/skills/`) | |
| Codex, Cursor, Copilot | `AGENTS.md` | — | |

## Decision

- Each repo has one **`AGENTS.md`** at its root: the rules, a map of the repo, the commands, and links into `docs/`. It holds the project rules that used to be in the global `~/.claude/CLAUDE.md`. The rules are project-specific, so they live with each project. No `CLAUDE.md` or `GEMINI.md`.
- **`.agents/`** holds the shared material:
  - `skills/<name>/SKILL.md`: step-by-step how-tos in the Agent Skills format (release, new task, review a PR, render the mockups);
  - `rules/`: only for a rule that must load for certain files.
- Claude Code reads skills only from `.claude/skills/`, so `scripts/setup-dev.ps1` makes `.claude/skills` a directory junction to `.agents/skills` (no admin rights needed; git-ignored).
- Project MCP servers, if any are ever needed, go in `.mcp.json`.

## Consequences

- One place to update the rules for every tool.
- A new clone runs `scripts/setup-dev.ps1` once.
- If a tool changes what it reads, this record gets replaced.
