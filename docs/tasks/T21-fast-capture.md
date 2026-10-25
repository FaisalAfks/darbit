# T21 Fast capture and benchmark

**Goal:** grab the screen faster and cheaper than `mss`, behind the same `screen.grab()`, and measure darbit's speed in CI so it doesn't get slower.

**Depends on:** nothing. **Milestone:** v0.3.

## Files

- `packages/darbit/src/darbit/platform/dxgi.py`: a DXGI Desktop Duplication grabber
- `packages/darbit/src/darbit/platform/screen.py`: picks the back end (`settings.capture = "auto" | "dxgi" | "mss"`)
- `benchmarks/bench.py`, `.github/workflows/ci.yml`: a benchmark job

## Steps

1. DXGI Desktop Duplication through `ctypes`/`comtypes` (or the small `dxcam` package if its licence and size are fine: decide in the PR). Keep the duplication object open between grabs; copy only the asked region from the staging texture.
2. It gives frames only when the screen changed; keep the last frame and return it when nothing changed (that's the speed-up for waits and observers).
3. Fall back to `mss` on any error (remote desktop, some laptops with two GPUs), once, with a log line.
4. Benchmarks: grab full screen and a 400×300 region, `exists` of a 60×40 target in a region and on the whole screen, an observer tick with five targets, CPU while `wait` runs for 10 s. Print a table; CI keeps the last result as an artifact and fails when something is 25% slower than the stored baseline.

## Done when

`grab()` of a region is at least 3× faster than with `mss` on the owner's PC, and the benchmark runs in CI.

## Tests

The back-end choice and the fallback with fakes; DXGI itself by hand (CI has no real display; the benchmark job uses `mss` there).
