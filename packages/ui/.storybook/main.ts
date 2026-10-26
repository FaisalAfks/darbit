// Storybook: every component in every theme (docs/decisions/0005-ui-process.md, docs/tasks/T03-components.md).
import type { StorybookConfig } from "@storybook/svelte-vite";

const config: StorybookConfig = {
  framework: "@storybook/svelte-vite",
  stories: ["../src/**/*.stories.ts"],
  addons: ["@storybook/addon-a11y"],
  core: { disableTelemetry: true },
  // the app's vite.config.ts builds the windows from src/apps; Storybook builds from the package itself
  viteFinal: (vite) => ({ ...vite, root: undefined, build: { ...vite.build, outDir: undefined, rollupOptions: undefined } }),
};

export default config;
