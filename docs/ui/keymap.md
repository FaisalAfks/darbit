# Keys

Every shortcut is in one file, [`src/darbit/keymap.toml`](../../src/darbit/keymap.toml). It can be overridden in `%APPDATA%\darbit\keymap.toml` (for you) or in a project's `darbit.toml` under `[keys]` (for that bot). Every shortcut is also a button, and hovering a button shows its key.

## Anywhere, even with the game in front

| Keys | Does |
|---|---|
| `Ctrl+Alt+C` | freeze the screen and capture |
| `Ctrl+Alt+H` | highlight what's found, with scores (again to hide) |
| `Ctrl+Alt+R` | record (again to stop) |
| `Ctrl+Alt+M` | mark a checkpoint while recording |
| `Ctrl+Alt+P` | pause or resume |
| `Ctrl+Alt+Q` | stop everything |

## In every darbit window

`Ctrl+K` command palette · `F1` keys for this screen · `Ctrl+Z` / `Ctrl+Y` undo and redo · `Ctrl+S` save · `Ctrl+Alt+T` next theme · `Ctrl+.` compact

## Capture

| Mouse | Does |
|---|---|
| click | box what's under the mouse; click again for the next bigger thing |
| drag | draw a box of the current kind |
| Shift + drag | draw a search region |
| Ctrl + click | set the click point |
| wheel | magnifier zoom |
| right-click | every action for what's under the mouse |

| Keys | Does |
|---|---|
| `Enter` / `Ctrl+Enter` | save / save and go to the next guide item |
| `Esc` | drop the selection; again to close |
| `Tab` | next kind: image, region, point |
| `Space` | new shot |
| `Alt` (held) | no snapping |
| `S` | snapping on or off |
| `Z` | pin the magnifier |
| `C` (held) | compare with the saved image |
| arrows, `Shift` | move 1 px, 10 px |
| `Ctrl` + arrows | resize |
| `Delete` | remove the selected box |
| `PgUp` / `PgDn` | previous / next guide item |

## Run panel

`F5` continue · `Shift+F5` stop · `F10` step · `F9` breakpoint · `F2` edit step · `Insert` add step
