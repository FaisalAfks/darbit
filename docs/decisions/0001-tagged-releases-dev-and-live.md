# 0001 Bots run tagged releases; development happens in a separate clone

Accepted, 2026-10-25.

## Context

ad-bot imported darbit straight from the development folder, with no version declared. Any change in progress could break the bot while it ran, and there was no way to tell which darbit a run used.

## Decision

- darbit is released by tagging `main` as `vX.Y.Z`. CI builds the wheel, with the built web UI, and attaches it to the GitHub release.
- A bot declares the darbit version it needs and gets it from that tag (`[tool.uv.sources]`, ADR 0003).
- Two copies of each repo:
  - a **dev clone** in `C:\Users\FMehm\Projects\<repo>`, with darbit installed editable from the dev clone;
  - a **live install** for running bots, `%LOCALAPPDATA%\darbit\bots\<bot>`, checked out at the bot's release tag with its own environment.
- Upgrading the live bot is a deliberate step: check out the new tag, then `uv sync`.
- The first release under this scheme is darbit **v0.2.0** (observers, state, run report, library check, capture engine).

## Consequences

- The running bot never changes underneath itself.
- Every bug report can name exact versions.
- A small release routine is needed for each change the live bot should get (a skill in `.agents/skills/release`).
