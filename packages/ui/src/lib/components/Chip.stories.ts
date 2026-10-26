// Chip in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Chip from "./Chip.svelte";

const meta = { title: "Basics/Chip", component: Chip } satisfies Meta<typeof Chip>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Running: Story = { args: {"text": "running", "tone": "ok"} };
export const Kind: Story = { args: {"text": "image", "tone": "image", "icon": "▣"} };
export const Update: Story = { args: {"text": "update v0.2.1", "tone": "info"} };
export const Failed: Story = { args: {"text": "no rewards", "tone": "danger"} };
