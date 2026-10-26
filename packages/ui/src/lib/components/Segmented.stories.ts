// Segmented in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Segmented from "./Segmented.svelte";

const meta = { title: "Controls/Segmented", component: Segmented } satisfies Meta<typeof Segmented>;
export default meta;
type Story = StoryObj<typeof meta>;

export const StudioSections: Story = { args: {"label": "Studio sections", "variant": "nav", "value": "overview", "items": [{"value": "overview", "label": "Overview", "icon": "◉"}, {"value": "flows", "label": "Flows", "icon": "⑂"}, {"value": "library", "label": "Library", "icon": "▣"}, {"value": "runs", "label": "Runs", "icon": "≡"}, {"value": "settings", "label": "Settings", "icon": "⚙"}]} };
export const Filters: Story = { args: {"label": "Show", "value": "all", "items": [{"value": "all", "label": "All 165"}, {"value": "risky", "label": "Risky 3"}, {"value": "missing", "label": "Missing 0"}]} };
export const CaptureKinds: Story = { args: {"label": "Kind", "value": "image", "items": [{"value": "image", "label": "Image"}, {"value": "region", "label": "Region"}, {"value": "point", "label": "Point"}]} };
