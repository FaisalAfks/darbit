"""The smallest darbit bot: wait for a button, click it, and repeat until stopped (Ctrl+Alt+Q).

Take the button's picture first, in darbit Studio's Capture (docs/guides/capture.md).
"""

import darbit as d

d.settings.timeout = 10  # how long a click waits for its target


def press_the_button() -> bool:
    """Click the button if it shows within the timeout. True if it was clicked."""
    clicked = d.click("Hello.Button")
    if not clicked:
        d.log("the button didn't show")
    return clicked


def main() -> None:
    while True:
        press_the_button()
        d.sleep(5)  # stoppable: Ctrl+Alt+Q ends the bot right here


if __name__ == "__main__":
    main()
