// The Studio shell from the approved layout (decision 0011), built only from components.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import StudioShell from "./stories/StudioShell.svelte";

const meta = {
  title: "Studio/Shell",
  component: StudioShell,
  parameters: { layout: "fullscreen" },
} satisfies Meta<typeof StudioShell>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Overview: Story = { args: { view: "overview" } };
export const WhereItComesFrom: Story = { args: { view: "overview", showSource: true } };
export const Flows: Story = { args: { view: "flows" } };
export const BotSwitcher: Story = { args: { view: "overview", sheet: "bots" } };
export const StudioSettings: Story = { args: { view: "overview", sheet: "app" } };
export const Commands: Story = { args: { view: "overview", palette: true } };
