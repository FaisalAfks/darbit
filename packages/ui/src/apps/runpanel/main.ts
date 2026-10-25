// runpanel: see docs/tasks/README.md for the task that builds this window.
import { mount } from "svelte";
import { connect, request } from "$lib/api";
import { listen, setKeymap } from "$lib/keymap";
import { applyTheme } from "$lib/theme";
import App from "./App.svelte";

applyTheme();
mount(App, { target: document.getElementById("app")! });

connect()
  .then(async () => {
    setKeymap(await request("keymap.get"), "run_panel");
    listen();
  })
  .catch(() => {
    // opened without darbit's server (e.g. npm run dev on its own): the app still shows, without data
  });
