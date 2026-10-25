# 0002 One darbit monorepo: library, web UI, VS Code extension

Accepted, 2026-10-25.

## Context

The library, the web UI and the VS Code extension share components, message types and the keymap. A separate `darbit-vscode` repo was planned and is still empty.

## Decision

One repo with workspaces:

```
packages/darbit/   the Python package (library + app extra), its tests
packages/ui/       the web UI (Svelte, Vite, Storybook); builds into the Python package
packages/vscode/   the VS Code extension (later)
docs/ assets/ examples/ scripts/ .agents/ .github/
```

- Python packages: a uv workspace. JavaScript packages: npm workspaces.
- One version for everything; one changelog.
- The `darbit-vscode` repo is deleted once it's confirmed empty.
- Bots are not part of the monorepo: each bot is its own repo (ad-bot).

## Consequences

- A UI change and the Python message it needs land in one PR.
- Installing from git needs `subdirectory = "packages/darbit"`.
- CI runs Python and JavaScript jobs side by side.
