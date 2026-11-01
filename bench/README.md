# Test bench

darbit's own search, run on saved screens whose answers are known: is each target found in the right place (or rightly not found), and how long does it take. Matching options are only recommended once the bench shows they help (rebuild plan, section 4).

```bash
uv run python bench/run.py                        # the made-up cases (made on first run), and bench/private
uv run python bench/run.py ../darbit-bench        # the real game screens
uv run python bench/run.py --options sizes,colour # with matching options on, as they come
```

- **Made-up cases** (`make_cases.py`): a 2560 x 1600 menu screen drawn from code, every target's place known; look-alikes and a missing picture that must not be found; the same screen at 1920 x 1200 (`option = "sizes"`) and a recoloured icon (`option = "colour"`) that only count with those options on. Generated, not committed.
- **Real cases** live in the private [darbit-bench](https://github.com/FaisalAfks/darbit-bench) repo; `from_screens.py` makes them from the screens darbit Studio saves. CI checks them out into `bench/private` when the `BENCH_TOKEN` secret is set.
- A case is a folder with `case.toml` (see `run.py`). The run exits 1 when an answer is wrong; speed is reported against the goals (10 ms in a region, 40 ms for the whole screen).

## Baseline (2026-10-30, before any option)

Plain full-colour template matching at the picture's own size, on the owner's PC:

| What | Result |
|---|---|
| Made-up menu, whole-screen searches (2560 x 1600) | right, 0.5–0.8 s each |
| Made-up menu, search inside a 1660 x 1080 panel | right, about 0.28 s |
| Made-up menu, search inside a 300 x 200 region | right, about 6 ms |
| A picture not on screen | rightly not found |
| The same icon in other colours (`colour`) | wrongly found at 0.875 |
| Targets at 1920 x 1200, taken at 2560 (`sizes`) | not found |
| ad-bot's Raid screen (JPEG), 4 whole-screen searches | right (0.99+), 0.4–0.6 s each |

## Matching options (2026-10-31)

The same cases with the options in `core/matching.py` turned on (`--options`), median of 5 searches per target. "Whole" is
a search of the 2560 x 1600 screen; "region" the searches inside a region (mostly the 1660 x 1080 panel).

| Options | Right | Whole, median | Whole, worst | Region, median |
|---|---|---|---|---|
| none | 14 of 14 | 572 ms | 701 ms | 274 ms |
| `grayscale` | 14 of 14 | 207 ms | 233 ms | 112 ms |
| `fast` | 14 of 14 | 48 ms | 57 ms | 33 ms |
| `colour` | 15 of 15 (the recoloured icon rightly not found) | 549 ms | 676 ms | 221 ms |
| `sizes` | 17 of 17 (the 1920 x 1200 targets found) | 612 ms | 3941 ms | 278 ms |
| `fast,grayscale` | 14 of 14 | 15 ms | 18 ms | 13 ms |
| `fast,grayscale,colour` | 15 of 15 | 16 ms | 23 ms | 14 ms |
| `fast,grayscale,colour,sizes` | 18 of 18 | 30 ms | 157 ms | 14 ms |

- `fast` with `grayscale` meets the 40 ms whole-screen goal with the same answers, the Raid JPEG screen included
- `colour` scores the share of pixels within a colour distance of 40: 0.94 and up on the JPEG screen, 0.07 for the recoloured icon
- `sizes` costs a search per size tried when the picture is missing at its own size; with `fast` the slowest is a picture not on screen at all (157 ms)

## `fast` checks candidates at half size first (2026-10-31)

`fast` used to check each of its 5 candidates at full size, more than half the time of a search inside the 1660 x 1080
panel. Now each is checked at half size (a quarter of the work), and only those within 0.06 of the best half-size
score get a full-size check, a few pixels around. Half-size scores were within 0.05 of full-size ones on every case,
the JPEG Raid screen included. The old and new `fast` matcher run back to back on the same machine, grayscale on,
median of 30 each:

| Target | Before | After |
|---|---|---|
| Char.3, Char.7 (in the panel) | 7.5–7.8 ms | 5.8–6.1 ms (−22%) |
| Char.0, Char.9 (look-alikes, whole screen) | 9.4–9.8 ms | 7.9–8.2 ms (−13 to −20%) |
| Menu targets (whole screen) | 8.7–12.8 ms | 6.3–8.5 ms (−28 to −33%) |
| Raid (JPEG, whole screen) | 7.5–8.2 ms | 5.3–6.2 ms (−25 to −30%) |
| Char.Missing | 9.6 ms | 9.2 ms |

Every answer is the same as before. On the owner's PC the panel searches took about 12 ms against the 10 ms goal;
22% less brings them to about 9.3 ms, to be measured there.

## Window space against screen pixels (2026-11-01)

`window-moved`: the menus with the game's window moved to 240, 180 and made 1920 x 1200 on the 2560 x 1600 desktop,
every target taken in it at 0, 0 and full size. Screen pixels need `sizes` to find them there; window space
(`[settings] space = "window"`) moves and scales each target with the window, and searches one with no region of its
own only inside the window. Median of 3 searches per target:

| Options | Right | Each search |
|---|---|---|
| `window` | 5 of 5 | 230–580 ms |
| `fast,grayscale,window` | 5 of 5 | 8–11 ms |
| `fast,grayscale,sizes` (screen pixels) | 5 of 5 | 73–122 ms |

Both find every target, and window space is about ten times quicker, because it knows the size instead of trying
each one. It still has to be measured on the owner's game (the window's title bar and borders, display scaling)
before it's recommended; screen pixels stay the default.
