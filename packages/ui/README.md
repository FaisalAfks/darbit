# darbit UI

The web front end of every darbit window: the hub, capture, highlight, the recorder bar and the run panel. The VS Code extension uses the same components.

```bash
npm install        # from the repo root (npm workspaces); versions are pinned exactly
npm run dev        # http://127.0.0.1:5173/<app>/ ; windows load from here with DARBIT_UI_DEV=1
npm run build      # into packages/darbit/src/darbit/ui/static/ (git-ignored, shipped in the wheel)
npm run check      # svelte-check and TypeScript
```

| Path | What |
|---|---|
| `src/lib/tokens/` | colours, sizes, motion and the themes ([design system](../../docs/style/ui/design-system.md)) |
| `src/lib/components/` | shared components |
| `src/lib/api.ts` | the connection to the local server |
| `src/lib/actions.ts` | every action, run by keys, buttons, the palette and menus alike |
| `src/lib/keymap.ts` | keys from `packages/darbit/src/darbit/keymap.toml` ([keys](../../docs/style/ui/keymap.md)) |
| `src/apps/<name>/` | one app per window |

Tasks: [docs/tasks](../../docs/tasks/README.md), T01 to T03 for this package.
