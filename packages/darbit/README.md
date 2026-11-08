# darbit

Simple GUI automation for Windows, in Python: find things on screen, click, type, wait. An improvement on SikuliX.

```python
import darbit as d

d.click("Gui.Play")
if d.wait("Lobby.Ready", timeout=10):
    d.press("q")
```

- `pip install darbit` for the library; `pip install "darbit[studio]"` adds darbit Studio and its tools, and `pip install "darbit[ocr]"` reading text (`d.read`).
- Docs, decisions and the roadmap: <https://github.com/FaisalAfks/darbit>.
