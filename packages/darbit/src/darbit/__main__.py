"""`python -m darbit`: the darbit command (cli.py), for when the darbit script isn't on the PATH."""

import sys

from .cli import main

sys.exit(main())
