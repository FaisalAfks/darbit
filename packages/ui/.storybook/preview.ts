// Every story gets the tokens, a theme from the toolbar, and a backdrop like the one it lives on.
import type { Preview } from "@storybook/svelte-vite";
import { THEMES, applyTheme, type ThemeName } from "../src/lib/theme";
import "./preview.css";

const preview: Preview = {
  globalTypes: {
    theme: {
      description: "Theme",
      toolbar: { title: "Theme", icon: "paintbrush", items: [...THEMES], dynamicTitle: true },
    },
    backdrop: {
      description: "What the component sits on",
      toolbar: { title: "Backdrop", icon: "photo", items: ["plain", "game"], dynamicTitle: true },
    },
  },
  initialGlobals: { theme: "glass-dark", backdrop: "game" },
  decorators: [
    (story, context) => {
      applyTheme(context.globals.theme as ThemeName);
      document.body.dataset.backdrop = context.globals.backdrop as string;
      return story();
    },
  ],
  parameters: {
    layout: "centered",
    a11y: { test: "error" },
  },
};

export default preview;
