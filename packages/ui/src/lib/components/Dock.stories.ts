// Dock in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Dock from "./Dock.svelte";

const meta = { title: "Studio/Dock", component: Dock } satisfies Meta<typeof Dock>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Tools: Story = { args: {"tools": [{"label": "Capture", "icon": "▣", "tone": "kind-image"}, {"label": "Highlight", "icon": "◎", "tone": "ok"}, {"label": "Record", "icon": "●", "tone": "danger"}, {"label": "Play", "icon": "▶", "tone": "accent-2"}, {"label": "Guide", "icon": "☰", "tone": "warn", "gap": true}, {"label": "Check", "icon": "✓", "tone": "info"}]} };
