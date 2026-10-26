// Readout in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Readout from "./Readout.svelte";

const meta = { title: "Capture/Readout", component: Readout } satisfies Meta<typeof Readout>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Image: Story = { args: {"kind": "image", "x": 1430, "y": 1118, "w": 420, "h": 94} };
export const Region: Story = { args: {"kind": "region", "x": 344, "y": 243, "w": 1515, "h": 1082} };
export const Point: Story = { args: {"kind": "point", "x": 1660, "y": 1165} };
