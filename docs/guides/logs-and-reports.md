# Logs, run reports and checking a library

What a script leaves behind, and how healthy its pictures are.

## Logs

Each day gets a log file in `.darbit/logs/` next to the script: what was looked for, found, clicked and pressed. A wait of 20 seconds or more that runs out also saves a screenshot (JPEG) in `.darbit/logs/screenshots/`; the newest 200 are kept. These are the failure screenshots the Overview links to, and `d.screenshot(label)` saves there too.

A script's own screenshots go into a folder of their own in `.darbit/logs/`, with their own limit, so they never push the failure screenshots out:

```python
shot = d.screenshot("raid", folder="rewards", keep=300)  # .darbit/logs/rewards, the newest 300 kept
d.record("rewards", shot=shot)  # "rewards/2026-11-10_12-00-00_raid.jpg": the file in .darbit/logs
```

`folder` is a folder inside `.darbit/logs/` (`"rewards"`, `"rewards/raid"`); one outside it, or `keep` under 1, raises `ValueError`. The name returned has the folder in front, except for `screenshots`.

## Run report

Next to each day's log, `.darbit/logs/report-<day>.jsonl` records every search (with the closest score when nothing was found), click and drag, and the script's own steps and events:

```python
with d.step("Daily quest"):  # timed; ends ok, failed (with a screenshot), interrupted or stopped
    ...
    d.record("quest done", quest="Wood")  # an event of the script's own
```

```
python -m darbit.tools.report                       # today's summary
python -m darbit.tools.report 2026-10-21 --logs ../my-bot/logs
```

The summary shows each step's runs, failures and times, why steps ended early, the targets most often not found with their closest score, and the script's events counted by name.

## Checking a library

```
python -m darbit.tools.check --screens shots/ --similarity 0.85
```

Scores every target in `images/` against the live screen, or against saved screenshots (one per app screen works best). Each target gets a verdict:

- **ok**: found in its region, nothing else on screen comes close
- **risky**: found, but something else scores almost as high and could be clicked by mistake
- **moved**: only found outside its region, so the region needs updating
- **not seen**: not on any screen checked

Results are added to `.darbit/state/check.jsonl`, to follow scores over time.
