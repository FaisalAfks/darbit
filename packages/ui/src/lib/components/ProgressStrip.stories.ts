// ProgressStrip in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import ProgressStrip from "./ProgressStrip.svelte";

const meta = { title: "Progress/ProgressStrip", component: ProgressStrip } satisfies Meta<typeof ProgressStrip>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Guide: Story = { args: {"done": 7, "total": 24} };
