# T29 Custom steps with `@d.action`

**Goal:** a bot author adds their own steps to the flow editor by marking a Python function. Its typed parameters become a form in the step palette.

**Depends on:** T27. **Milestone:** v0.5. **Decision:** [ADR 0007](../decisions/0007-studio-flows-and-actions.md).

## How

```python
@d.action("Pick a character", category="Speed Raid")
def pick_character(name: str, slide: int = 0) -> bool:
    """Scroll the list to a character and select it."""
    ...
```

- **In the palette:** the action shows under its category, with a form built from its parameters:
  - `str`, `int`, `float`, `bool`;
  - a target name, which gets a picker;
  - a key, which gets a key picker.

  Its docstring is the help text.
- **In a flow:** it's saved as `call: ad_bot.speed_raid.pick_character` with its arguments. Exported to Python, it's a normal call.
- **Its result**, if it returns one, can be used by a check or saved with `set`.
- **Discovery:** the Studio finds actions by importing the bot's modules listed in `darbit.toml` (`[flows] actions = ["ad_bot.actions"]`).

## Files

- `packages/darbit/src/darbit/runs/actions.py`: the decorator and the registry
- `packages/darbit/src/darbit/server/…`: `actions.list` for the palette

## Done when

An ad-bot action with three parameter kinds shows in the palette with a working form, and runs from a flow.
