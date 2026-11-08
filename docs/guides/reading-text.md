# Reading text

Reading numbers, timers and words off the screen: `d.read`, `d.read_number` and `d.read_time`. Why it works this way: [decision 0019](../decisions/0019-reading-text.md).

## Install

Reading needs the `ocr` extra (RapidOCR and its models, about 45 MB):

```bash
pip install "darbit[ocr]"     # or, in a checkout: uv sync --extra ocr
```

Without it, the first read warns once and every read is `None`; `import darbit` works either way.

## Reading

```python
import darbit as d

coins = d.read_number("Shop.Coins")  # a named Region showing 4.99M: 4990000.0
left = d.read_time("Run.Timer")  # 02:31: 151.0 seconds
title = d.read(d.Region(100, 40, 300, 40))

found = d.exists("Shop.Price.Tag")
if found:
    price = found.read_number()  # inside the found Image's box
```

| Call | Gives |
|---|---|
| `read(where, chars=None)` | the text, or `None` |
| `read_number(where)` | a number: `1,234` 1234.0, `4.99M` 4990000.0, `126.62B`, `1.5k` 1500.0, `12%` 12.0, `1,5` 1.5; or `None` |
| `read_time(where)` | seconds: `02:31` 151.0, `1:02:03` 3723.0, `2m 30s` 150.0, `45s`, `1h 5m`, `1d 2h`; or `None` |

`where` is any of:

- a **Region** (`d.Region(x, y, w, h)`, `d.area("Shop.List")`) or a **Match**: read inside it;
- the **name of a Region** taken with the capture tool: read where it is now (in window space it follows the window);
- the **name of an Image**: read inside where it's found now (one look; `None` when it isn't on screen).

The same calls are methods: `region.read()`, `region.read_number()`, `region.read_time()`, and `match.read()` and the others on a Match.

`None` means the text couldn't be read, was read with less than `settings.read_confidence` (0.5), or isn't a number or time. A read never raises for what's on screen; a name that isn't a Region or an Image is a mistake (`TargetError`), like in `d.area`.

## What a Region holds

A Region's `.json` can say what text it holds, and a read in it then uses only those characters:

```json
{"kind": "region", "region": [2133, 404, 160, 48], "text": "digits"}
```

- `"digits"`: 0 to 9
- `"number"`: digits and `. , % + -` and the suffixes `k M B T` (what `read_number` uses unless the Region says otherwise)
- `"time"`: digits and `: . h m s d` and spaces (what `read_time` uses)
- anything else: the characters themselves, e.g. `"0123456789/"` for `12/50`

Limiting the characters happens inside the recogniser, so a `0` wins where an `O` was only a little likelier. `d.read(where, chars="digits")` does the same for one call.

## How a read works

1. The Region is grabbed from the screen.
2. It's prepared, if asked (below).
3. **One line:** it's cut to the text in it and goes straight to the recogniser, about 10 ms on 4 threads. A Region with room around small text is fine: the cut takes it away.
4. A line that comes back empty or unsure is read again **line by line**: the text is found first, each line read, and the lines joined with `\n` (15 to 50 ms).

Each read is logged with what was read and how sure it was, and recorded in the run report as a `read`, `read_number` or `read_time` event with `text`, `confidence`, `counted` and `ms`.

## Options

In `darbit.toml` for the whole bot, or as `"read"` in a Region's `.json` for one Region (on top of the bot's):

```toml
[settings]
read_confidence = 0.6   # lowest confidence that counts (0.5)
read_threads = 2        # CPU threads a read uses (4)

[settings.read]
upscale = 2             # resize first: text only a few pixels high (true: 2)
invert = true           # dark text on a light background
threshold = true        # black and white first (true: by Otsu's method, or a grey level 1 to 255)
lines = true            # always find the lines first: several lines, or text in a busy Region
trim = false            # don't cut a single line to its text
```

All are off by default (`trim` is on). Measure an option on your own screens with `darbit bench` before turning it on.

`settings.reader` picks another reader installed as a plugin (the `darbit.readers` entry point); the default is `"rapidocr"`.

## On the test bench

A case's `case.toml` can check reads, judged and timed with the searches:

```toml
[[read]]
target = "Shop.Coins"          # a named Region (or region = [x, y, w, h])
number = 4990000               # or text = "Daily quest", or time = 151

[[read]]
region = [56, 126, 119, 72]
text = "1,234"
chars = "0123456789,"          # only for a text read: the characters it may use
```

`darbit bench cases --options lines` turns a reading option on for the run. Without the `ocr` extra, reads show as `needs ocr` and aren't counted.
