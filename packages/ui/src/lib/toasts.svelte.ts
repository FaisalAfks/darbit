// Short messages in the corner: `toast("Capture saved", "tool")`. One line each, three at most, gone after
// 3 s. Shown by <Toast /> once per window.

export interface Message {
  id: number;
  slot: "tool" | "bot" | "guide";
  text: string;
  from?: string; // the bot's name, for the bot slot
}

const SHOWN_FOR = 3000; // ms
const MOST = 3;

let next = 1;
export const messages: Message[] = $state([]);

export function toast(text: string, slot: Message["slot"] = "tool", from?: string): void {
  const message = { id: next, slot, text, from };
  next += 1;
  messages.push(message);
  while (messages.length > MOST) messages.shift();
  setTimeout(() => {
    const index = messages.findIndex((shown) => shown.id === message.id);
    if (index >= 0) messages.splice(index, 1);
  }, SHOWN_FOR);
}
