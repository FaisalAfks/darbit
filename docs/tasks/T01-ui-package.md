# T01 UI package and build

**Goal:** one web front end in `ui/`, TypeScript and Svelte 5, built by Vite into `packages/darbit/src/darbit/ui/static/` with one entry page per window.

**Depends on:** nothing. **Issue:** #45. **Milestone:** v0.3.

## Files

- `ui/package.json`, `ui/tsconfig.json`, `ui/vite.config.ts`, `ui/svelte.config.js`: already sketched
- `packages/ui/src/apps/{hub,capture,recorder,runpanel,highlight}/index.html` + `main.ts` + `App.svelte`
- `packages/darbit/src/darbit/ui/__init__.py`: `static_dir()`, already there
- `.gitignore`: `ui/node_modules/`, but **not** `packages/darbit/src/darbit/ui/static/` (the build is committed for releases only, see step 5)

## Steps

1. `npm install` in `ui/` with the versions in `package.json` (pin exact versions; no `^`).
2. Vite multi-page build: each `src/apps/<name>/index.html` is an input; the output is `packages/darbit/src/darbit/ui/static/<name>/index.html` plus shared hashed chunks in `static/assets/`. The config is in `vite.config.ts`.
3. `npm run dev` serves every app on `http://127.0.0.1:5173/<name>/`. With `DARBIT_UI_DEV=1`, the desktop windows (T06) load from the dev server instead of `static/`, so changes show without a rebuild.
4. Path alias `$lib` → `packages/ui/src/lib`.
5. Release builds: CI (later, T25) runs `npm ci && npm run build` before building the wheel. Until then the static folder is built by hand before tagging. During development it's git-ignored by a `static/.gitignore` with `*` and `!.gitignore`.
6. Budget: each app's first load ≤ 60 kB of JS gzipped (the capture app may add Konva, ≤ 150 kB). Print sizes with `npm run build -- --report` and put them in the PR.

## Contracts

- App names: `hub`, `capture`, `recorder`, `runpanel`, `highlight`. T06 opens windows by these names.
- Every app starts with `connect()` from `$lib/api.ts` (T05) and `applyTheme()` from `$lib/theme.ts` (T02).

## Done when

- `npm run build` produces the five pages; opening `static/hub/index.html` from a local server shows the placeholder app in the default theme.
- The sizes are within budget.

## Tests

- `npm run check` (svelte-check, TypeScript) passes.
- `packages/darbit/tests/test_scaffold.py` checks `darbit.ui.static_dir()` points inside the package.

## Not in this task

Real screens. Each app only shows its name and a theme switch.
