// The components together, as the Studio's Overview uses them (docs/ui/mockups.html, decision 0011).
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import OverviewDemo from "./stories/OverviewDemo.svelte";

const meta = {
  title: "Studio/Overview tiles",
  component: OverviewDemo,
  parameters: { layout: "padded" },
} satisfies Meta<typeof OverviewDemo>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Tiles: Story = { args: { showSource: false } };
export const WhereItComesFrom: Story = { args: { showSource: true } };
