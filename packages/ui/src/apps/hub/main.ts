// darbit Studio: connects first, then shows the app with or without the server. See docs/tasks/T20-hub.md.
// With ?view=pill&path=… it's the run pill instead (desktop/pill.py).
import { mount } from "svelte";
import { connect, request } from "$lib/api";
import { listen, setKeymap } from "$lib/keymap";
import { startTheme } from "$lib/theme";
import App from "./App.svelte";
import RunPill from "./RunPill.svelte";

startTheme();

const params = new URLSearchParams(location.search);
const target = document.getElementById("app")!;

connect()
  .then(async () => {
    setKeymap(await request("keymap.get"), "hub");
    listen();
    if (params.get("view") === "pill") mount(RunPill, { target, props: { path: params.get("path") ?? "" } });
    else mount(App, { target, props: { connected: true } });
  })
  .catch(() => {
    // opened without darbit's server (e.g. npm run dev on its own): the app says how to start it
    mount(App, { target, props: { connected: false } });
  });
