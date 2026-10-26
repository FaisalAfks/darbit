// ScoreBadge in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import ScoreBadge from "./ScoreBadge.svelte";

const meta = { title: "Basics/ScoreBadge", component: ScoreBadge } satisfies Meta<typeof ScoreBadge>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Ok: Story = { args: {"score": 0.97} };
export const Risky: Story = { args: {"score": 0.88, "similarity": 0.85, "note": "Luffy 0.82"} };
export const Missing: Story = { args: {"score": null} };
