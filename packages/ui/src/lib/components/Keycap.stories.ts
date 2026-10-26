// Keycap in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Keycap from "./Keycap.svelte";

const meta = { title: "Basics/Keycap", component: Keycap } satisfies Meta<typeof Keycap>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Shortcut: Story = { args: {"keys": "ctrl+alt+c"} };
export const Pressed: Story = { args: {"keys": "ctrl+alt+r", "down": true} };
