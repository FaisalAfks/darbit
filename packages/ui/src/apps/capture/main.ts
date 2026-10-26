// Capture: the overlay on the frozen screen, or with ?view=next the bar between guide items (desktop/capture_window.py).
import { mount } from "svelte";
import { connect, request } from "$lib/api";
import { listen, setKeymap } from "$lib/keymap";
import { startTheme } from "$lib/theme";
import App from "./App.svelte";
import NextBar from "./NextBar.svelte";

startTheme();

const target = document.getElementById("app")!;
const view = new URLSearchParams(location.search).get("view");

connect()
  .then(async () => {
    setKeymap(await request("keymap.get"), "capture");
    listen();
    if (view === "next") mount(NextBar, { target });
    else mount(App, { target });
  })
  .catch(() => {
    target.textContent = "Capture needs darbit's local server: open it from darbit Studio.";
  });
