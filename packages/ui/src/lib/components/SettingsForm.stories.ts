// A bot's settings page made from its settings.toml (T18), with settings like ad-bot's.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import SettingsForm, { type Section } from "./SettingsForm.svelte";

const SECTIONS: Section[] = [
  {
    key: "modes",
    label: "Modes",
    help: "What the bot plays each round.",
    settings: [
      { key: "modes.raid", type: "bool", default: true, label: "Raid", help: "Every round, at the raid hour.", rules: {} },
      { key: "modes.speed_raid", type: "bool", default: true, label: "Speed Raid", help: "The next character, every 30 minutes.", rules: {} },
      { key: "modes.afk", type: "bool", default: false, label: "AFK", help: "Claim the AFK rewards.", rules: {} },
    ],
  },
  {
    key: "speed_raid",
    label: "Speed Raid",
    help: "",
    settings: [
      { key: "speed_raid.every_minutes", type: "int", default: 30, label: "Every (minutes)", help: "How often to try the next character.", rules: { min: 10, max: 120 } },
      { key: "speed_raid.order", type: "choice", default: "list", label: "Order", help: "The list's order, or used ones last.", rules: { options: ["list", "unused first"] } },
    ],
  },
  {
    key: "controls",
    label: "Controls",
    help: "",
    settings: [
      { key: "controls.skills", type: "keys", default: "54132", label: "Skills, in order", help: "Pressed in this order in a fight.", rules: {} },
      { key: "controls.assists", type: "keys", default: "er", label: "Assists", help: "", rules: {} },
    ],
  },
  {
    key: "regions",
    label: "Regions",
    help: "",
    settings: [
      { key: "regions.main_menu", type: "region", default: [344, 243, 1515, 1082], label: "Main menu", help: "Where the menus open.", rules: {} },
      { key: "regions.afk_spot", type: "location", default: [1660, 1165], label: "AFK spot", help: "Clicked to stay active.", rules: {} },
    ],
  },
];

const meta = {
  title: "Studio/SettingsForm",
  component: SettingsForm,
  parameters: { layout: "padded" },
} satisfies Meta<typeof SettingsForm>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Defaults: Story = { args: { sections: SECTIONS, values: {} } };
export const Changed: Story = {
  args: { sections: SECTIONS, values: { "modes.afk": true, "speed_raid.every_minutes": 45, "controls.skills": "12345" } },
};
export const WhereItComesFrom: Story = { args: { sections: SECTIONS, values: {}, showSource: true } };
