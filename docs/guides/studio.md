# darbit Studio

darbit Studio is a window onto darbit's service: pick a bot, run, pause and stop it, and see what it's doing. It's built with Qt (PySide6 and QML) and needs the `studio` extra:

```bash
pip install "darbit[studio]"     # or, in a checkout: uv sync --extra studio
darbit app
```

![The Overview](../ui/images/qt-studio-overview.png)

- **Bots:** the bot menu at the top left lists every bot, with **New bot** (from darbit's template, from a git link, or a
  folder you have) and **darbit settings**. darbit settings can put the bots in a sidebar instead, which folds to their
  squares on a narrow window. The Studio opens on the bot shown last.
- **Overview** (Ctrl+1): what the bot is doing now and today's round as a bar, then a line for anything that needs you
  (pictures still to take, the last problem), the round, progress, what's next and gains.
- **Library** (Ctrl+2): every picture, point and area, with its last score against the similarity it needs. Search
  (Ctrl+F), filter by kind, Missing or Weak, sort by name, weakest or most used, and group by name or kind if you like.
  Click one for the inspector: its numbers and last scores, **Retake**, **Rename** (every line of code naming it changes
  too), **Delete**, and where it's used.

  ![The Library](../ui/images/qt-studio-library.png)
- **Capture** (the Library's Capture button): the Studio steps aside, the screen is frozen, and it opens full screen.
  Click something to box it (again for bigger, right-click for smaller) or drag a box; the handles and the arrow keys
  change it (Shift: 10 px, Ctrl: its size). Image, Region or Point; **T** tests it (every match, with its score);
  name it and press **Enter** to save; **Esc** closes. With a setup guide, the next picture to take is shown.
- **Results** (Ctrl+3): the bot's days; the chosen one in a sentence, its problems, what it got (today, the week, the
  total) and a timeline of its modes, from the run history.
- **Settings** (Ctrl+4): the bot's `settings.toml` as a form, by section; a changed value gets a dot and a save bar
  slides up (Ctrl+S saves).
- **The run control** (top right): Play (F5); while running, its time with Pause and Stop.
- **darbit settings** (Ctrl+,): the theme, the bot sidebar, and smooth effects (off for a slower PC). A `theme.toml` in
  darbit's settings folder lays tokens over the theme (`base = "glass-dark"`, `accent = "#ff7ab6"`).

Closing the Studio stops nothing: bots run in the service, which keeps going (see [the service](service.md)). The tray icon opens it again.

The pages follow the mockups in `docs/ui/` and the tokens in [the design system](../style/ui/design-system.md); `darbit.studio.app.shot()` draws any page into a PNG with no screen, which the tests use for every page and theme.

Highlight, the recorder and the action editor come next (rebuild plan, milestone 4).
