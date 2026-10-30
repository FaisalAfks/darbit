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
