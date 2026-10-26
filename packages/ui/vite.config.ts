// One page per window, built into the Python package. See docs/tasks/T01-ui-package.md.
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { resolve } from "node:path";
import { defineConfig } from "vite";

const apps = ["hub", "capture", "highlight", "recorder", "runpanel"];

export default defineConfig({
  root: "src/apps",
  base: "./",
  plugins: [svelte()],
  resolve: { alias: { $lib: resolve(import.meta.dirname, "src/lib") } },
  server: { host: "127.0.0.1", port: 5173, strictPort: true },
  build: {
    outDir: resolve(import.meta.dirname, "../darbit/src/darbit/ui/static"),
    emptyOutDir: true, // git-ignored; the wheel ships it (artifacts in packages/darbit/pyproject.toml)
    target: "es2022", // WebView2 and VS Code are recent Chromium
    rollupOptions: {
      input: Object.fromEntries(apps.map((app) => [app, resolve(import.meta.dirname, `src/apps/${app}/index.html`)])),
    },
  },
});
