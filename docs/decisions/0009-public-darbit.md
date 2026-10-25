# 0009 darbit public from v0.2.0, ad-bot private

Accepted, 2026-10-25.

## Context

On GitHub Free, private repos can't use rulesets (branch protection), GitHub Pages or Discussions. The API answers 403. darbit is meant to be shared, and since August 2026 another project uses the name `darbit` (an unrelated machine-learning repo, not on PyPI). ad-bot automates a game and is personal.

## Decision

- **Going public:** darbit becomes public when v0.2.0 is released, after:
  1. a secret scan of its whole history (gitleaks);
  2. a check that it contains no private game data;
  3. a final confirmation by the owner.
- **Once public, darbit gets:**
  - a ruleset on `main`: pull request required, CI must pass, squash merges only, no force pushes;
  - GitHub Pages for the docs site;
  - Discussions, with an Ideas category, which replaces the local `IDEAS.md` for tool ideas.
- **The name stays `darbit`.** Claiming it on PyPI is the next step once the release process is in place.
- **ad-bot stays private.** It gets the same templates, CI and releases, without rulesets.

## Consequences

- Commits and issues become visible; the commit e-mail can be switched to GitHub's noreply address for new commits.
- ad-bot installs darbit from the public tag with no token needed.
