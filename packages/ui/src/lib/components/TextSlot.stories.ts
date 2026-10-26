// TextSlot in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import TextSlot from "./TextSlot.svelte";

const meta = { title: "Basics/TextSlot", component: TextSlot } satisfies Meta<typeof TextSlot>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Bot: Story = { args: {"slot": "bot", "from": "ad-bot", "text": "The green Equip button, without the shadow under it."} };
export const Guide: Story = { args: {"slot": "guide", "text": "Open the Bag and go to the Characters tab."} };
export const Tool: Story = { args: {"slot": "tool", "text": "click again for bigger · right-click smaller"} };
