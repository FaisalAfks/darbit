// Button in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Button from "./Button.svelte";

const meta = { title: "Basics/Button", component: Button } satisfies Meta<typeof Button>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {"label": "Run", "icon": "▶"} };
export const Primary: Story = { args: {"label": "Install a bot", "icon": "＋", "variant": "primary"} };
export const Danger: Story = { args: {"label": "Stop", "icon": "■", "variant": "danger"} };
export const Quiet: Story = { args: {"label": "Restore defaults", "variant": "quiet"} };
export const Small: Story = { args: {"label": "Capture again", "size": "s"} };
export const Disabled: Story = { args: {"label": "Save", "variant": "primary", "disabled": true} };
