// StepRow in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import StepRow from "./StepRow.svelte";

const meta = { title: "Flows/StepRow", component: StepRow } satisfies Meta<typeof StepRow>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Checkpoint: Story = { args: {"number": "1", "kind": "checkpoint", "text": "Checkpoint Wave 1 waits for Dim.Game.Left up to 30 s", "chip": "0.84"} };
export const Loop: Story = { args: {"number": "5", "kind": "loop", "text": "Repeat until Dim.Game.Leave shows", "chip": "loop", "selected": true} };
export const Nested: Story = { args: {"number": "5.2.1", "kind": "call", "depth": 2, "text": "dodge()", "chip": "function"} };
export const WithNote: Story = { args: {"number": "6", "kind": "input", "text": "Click Dim.Game.Leave", "note": "back to the lobby"} };
export const Code: Story = { args: {"number": "5.3", "kind": "code", "text": "Code, kept word for word", "chip": "code"} };
