// darbit Studio: connects first, then shows the app with or without the server. See docs/tasks/T20-hub.md.
import { mount } from "svelte";
import { connect, request } from "$lib/api";
import { listen, setKeymap } from "$lib/keymap";
import { startTheme } from "$lib/theme";
import App from "./App.svelte";

startTheme();

connect()
  .then(async () => {
    setKeymap(await request("keymap.get"), "hub");
    listen();
    mount(App, { target: document.getElementById("app")!, props: { connected: true } });
  })
  .catch(() => {
    // opened without darbit's server (e.g. npm run dev on its own): the app says how to start it
    mount(App, { target: document.getElementById("app")!, props: { connected: false } });
  });
