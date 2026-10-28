// The recorder bar (desktop/record_window.py): mounts once connected, since it only shows a live recording.
import { mount } from "svelte";
import { connect, request } from "$lib/api";
import { listen, setKeymap } from "$lib/keymap";
import { startTheme } from "$lib/theme";
import App from "./App.svelte";

startTheme();

const target = document.getElementById("app")!;

connect()
  .then(async () => {
    setKeymap(await request("keymap.get"), "app");
    listen();
    mount(App, { target });
  })
  .catch(() => {
    target.textContent = "The recorder needs darbit's local server: start it from darbit Studio.";
  });
