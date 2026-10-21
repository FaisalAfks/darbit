# T19 darbit new, install and run

**Goal:** one `darbit` command for everything: make a project, install one from git, run it, and open the tools.

**Depends on:** T17. **Issue:** #52. **Milestone:** v0.5.

## Commands

| Command | Does |
|---|---|
| `darbit new NAME` | a project folder: `darbit.toml`, `settings.toml`, `bot.py`, `guide.toml`, `images/`, `.gitignore` |
| `darbit install GIT_URL` | clones into `%USERPROFILE%\darbit\bots\<name>`, installs its `requirements.txt` into its own venv, creates `config.toml`, opens the setup guide if images are missing |
| `darbit run [PATH]` | runs the project's entry with its venv |
| `darbit capture …`, `darbit guide`, `darbit highlight`, `darbit record NAME`, `darbit play FILE`, `darbit check`, `darbit report` | the tools (today's `python -m darbit.*` modules) |
| `darbit app` | opens the hub |
| `darbit keys` | prints the keymap and its conflicts |

## Files

- `src/darbit/cli.py`: `main()` with subcommands calling the existing modules
- `pyproject.toml`: `[project.scripts] darbit = "darbit.cli:main"`

## Steps

1. `argparse` subcommands that hand their arguments to each tool's `main(argv)` (they all have one).
2. `new` writes files from templates in `src/darbit/project/templates/`.
3. `install`: `git clone --depth 1`, `python -m venv`, `pip install -r`, then `darbit` itself in that venv at the version the manifest asks for.
4. `run`: sets the working folder, starts the entry, forwards Ctrl+C.

## Done when

`darbit install https://github.com/FaisalAfks/ad-bot` on a clean user account ends with the bot ready to set up.

## Tests

Argument parsing per command; `new` writes the expected files; `install` with a local bare repo in `tmp_path` (no network).
