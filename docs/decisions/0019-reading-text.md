# 0019 Reading text: RapidOCR as an optional extra, one line straight to the recogniser

Accepted, 2026-11-08.

## Context

Bots need to read what a game shows as text: coins (`4.99M`), counts (`1,234`), timers (`02:31`), labels. Until now
a bot could only match images, so every number was a picture per digit or not read at all (#55). The rebuild plan
has a `Reader` interface for this; nothing was behind it.

What a reader needs here: small, light text on busy game backgrounds, read in a few milliseconds on a CPU that is
also running the game, installed with pip and nothing else, under a license that fits darbit's MIT/Apache-2.0.

Options weighed:

| Option | For | Against |
|---|---|---|
| **RapidOCR** on onnxruntime | PaddleOCR's PP-OCR models without Paddle; pure pip; models in the wheel; Apache-2.0 | depends on `opencv-python-headless` (below) |
| Windows' built-in OCR (`Windows.Media.Ocr`) | nothing to install | Windows only; language packs; weaker on stylised digits; a second backend later (#399) |
| EasyOCR | good accuracy | PyTorch: hundreds of MB |
| PaddleOCR | the models' own home | the Paddle framework: large, heavy to install |
| Tesseract | well known | a separate program to install; weak on game fonts and coloured backgrounds |

What was checked (2026-11-08):

- **Package:** `rapidocr` 3.10.0 on PyPI (the older `rapidocr_onnxruntime` stopped at 1.4.4), `License-Expression:
  Apache-2.0`, Python 3.8 and up, a 27.3 MB wheel. It doesn't bring an inference engine; darbit adds `onnxruntime`
  (1.31.1, MIT, a 14.9 MB wheel on Windows).
- **Models:** the wheel bundles PP-OCRv6 small (text finder 9.9 MB, recogniser 21.2 MB) and a 0.6 MB angle classifier.
  Its `MODEL_LICENSES.md` lists them as Apache-2.0, converted from PaddleOCR's official models, and PaddlePaddle's
  model card for `PP-OCRv6_small_rec_onnx` says `license: apache-2.0`. PP-OCRv5 mobile (finder 4.8 MB, English
  recogniser 7.9 MB) is no longer bundled: RapidOCR downloads it from modelscope.cn on first use, and it isn't
  covered by that notice.
- **Speed** (this PC, a game running, 4 threads): a short number in a loose Region reads in about 10 ms with the
  recogniser alone (15 ms on 2 threads, 26 ms on 1), 15 to 47 ms with the text finder first; the first read takes
  about a second (import and model load). onnxruntime's default of every core made a read about 20 times slower on a
  busy PC, and RapidOCR's default enlarging of small crops for the finder took seconds.
- **Accuracy:** on drawn text (`4.99M`, `126.62B`, `1,234`, `02:31`, `1:02:03`, `2m 30s`, "Daily quest") every
  read was right at 0.99 and up, once the crop was cut to the text. The recogniser squeezes a line to 48 px high, so a
  Region with a lot of room around small text misread (`499m`, `0283`) until it was trimmed.

## Decision

- **Reading is behind the `Reader` interface** (`platform/backend.py`: `line(pixels, allowed)` and
  `lines(pixels, allowed)`), picked by `settings.reader` like matchers; plugins add readers under the `darbit.readers`
  entry point.
- **The default reader is RapidOCR with its bundled PP-OCRv6 small models on onnxruntime,** in the optional extra
  `darbit[ocr]` (`rapidocr>=3.10,<4`). Bundled models mean no download on a bot's first read and a license notice
  that covers them; PP-OCRv5 mobile would be smaller but downloaded at run time.
- **The API:** `d.read(where, chars=None)`, `d.read_number(where)`, `d.read_time(where)` (seconds), and the same on
  `Region` and `Match`. `where` is a Region, a Match, a named Region or a named Image (read inside where it's found).
  Text that can't be read, or is read with less than `settings.read_confidence` (0.5), is None; without the extra the
  first read warns once and every read is None.
- **A single line goes straight to the recogniser,** cut to its text first, without the text finder; one that comes
  back empty or unsure is read again line by line. `lines = true` always finds lines first (several lines of text).
- **A read can be limited to some characters,** decoding the recogniser's output with only those (so a 0 wins over a
  likelier O): `"text": "digits"` (or `"number"`, `"time"`, or the characters) in a Region's .json, or `chars=`.
  `read_number` and `read_time` use the number and time characters unless the Region says otherwise.
- **Preparing options** (`upscale`, `invert`, `threshold`) are off by default, in `[settings.read]` or a Region's
  `"read"`, and measured on the bench before they're recommended. `settings.read_threads` (4) sets onnxruntime's
  threads.
- **Each read is logged and recorded with its confidence** (`read`, `read_number`, `read_time` events), and the test
  bench judges and times `[[read]]` entries.
- **Later:** Windows' built-in OCR as a second reader (#399); text targets, found by what they say (#400).

## Consequences

- `import darbit` stays free of the extra; RapidOCR is imported on the first read.
- RapidOCR depends on `opencv-python-headless`, darbit on `opencv-python`: both install the same `cv2` files. They
  are the same OpenCV at the same version, and darbit uses nothing of the GUI part, so either copy works; uninstalling
  one of them leaves `cv2` broken until the other is installed again. Since #406 darbit depends on
  `opencv-python-headless` too, so an environment has one OpenCV.
- Reading with some characters uses RapidOCR's recogniser below its public call (its model session, resizing and
  alphabet), so the extra is pinned below RapidOCR 4 and the tests with the real models run in CI.
- The Windows `python` job and the `bench` job install the extra; `python-linux` doesn't, so the tests that need the
  models show they skip cleanly without it.
