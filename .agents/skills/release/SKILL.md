---
name: release
description: Release a new darbit version (SemVer tag, GitHub release with the wheel and notes) and bump a bot to it.
---

# Release darbit

1. Make sure `main` is green in CI and everything for the release is merged.
2. On a branch `release/vX.Y.Z`:
   - set `version` in `packages/darbit/pyproject.toml`;
   - in `CHANGELOG.md`, rename `## Unreleased` to `## X.Y.Z - YYYY-MM-DD` and start a new empty `## Unreleased` above it;
   - open a PR "Release vX.Y.Z" that says `Closes #<release issue>`. The owner merges.
3. After the merge, tag `main`: `git tag vX.Y.Z && git push origin vX.Y.Z`. The release workflow builds the wheel and makes the GitHub release, with notes generated from the PR labels.
4. Check the release has the wheel, and that its notes read well. Edit them in the owner's voice if needed.
5. To move a bot to the new version, open a PR in the bot's repo:
   - change the `tag` in its `[tool.uv.sources]`;
   - run `uv lock`;
   - run its tests;
   - after the merge, tag the bot too.

   The live install upgrades with `git checkout <bot tag>` then `uv sync` (darbit decision 0001).

SemVer: a fix is a patch (0.2.1), a new feature a minor (0.3.0); before 1.0 a breaking change is also a minor, noted in the changelog.
