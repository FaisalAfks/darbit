# darbit

Simple GUI automation for Windows, in Python: find things on screen, click, type, wait. An improvement on SikuliX, with input that games accept, targets that carry their own settings, tools to capture and check them, and, coming next, **darbit Studio**: install and run bots, and build them from recorded flows without code.

```python
import darbit as d

if d.click("Gui.Play"):
    d.press("tab")
```

| Start here | |
|---|---|
| [Getting started](getting-started.md) | install, a first script, capturing targets |
| [Guides](guides/targets-and-calls.md) | targets and calls, observers and state, logs and reports, the capture tool |
| [Architecture](architecture/index.md) | how the code fits together |
| [API reference](reference/api.md) | every public call |
| [Code style](style/code.md), [writing style](style/writing.md), [UI design system](style/ui/design-system.md) | how things are written and designed |
| [Decisions](decisions/README.md), [roadmap](roadmap.md), [tasks](tasks/README.md) | why, what's next, and how to build it |
| [UI mockups](ui/mockups.html) | darbit Studio and its tools, before they're built |
