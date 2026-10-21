# darbit UI

The web front end of every darbit window: the hub, capture, highlight, the recorder bar and the run panel. The VS Code extension uses the same components.

```bash
npm install
npm run dev        # http://127.0.0.1:5173/<app>/ ; windows load from here with DARBIT_UI_DEV=1
npm run build      # into ../src/darbit/ui/static/
npm run check
```

| Path | What |
|---|---|
| `src/lib/tokens/` | colours, sizes, motion and the themes ([design system](../docs/ui/design-system.md)) |
| `src/lib/components/` | shared components |
| `src/lib/api.ts` | the connection to the local server |
| `src/lib/actions.ts` | every action, run by keys, buttons, the palette and menus alike |
| `src/lib/keymap.ts` | keys from `src/darbit/keymap.toml` ([keys](../docs/ui/keymap.md)) |
| `src/apps/<name>/` | one app per window |

Tasks: [docs/tasks](../docs/tasks/README.md), T01 to T03 for this package.
