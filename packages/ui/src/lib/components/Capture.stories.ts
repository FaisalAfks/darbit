// Capture's controls together: toolbar, readouts (click one to type) and the magnifier.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import CaptureDemo from "./stories/CaptureDemo.svelte";

const meta = { title: "Capture/Controls", component: CaptureDemo } satisfies Meta<typeof CaptureDemo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Controls: Story = {};
