# Writing style

For everything public: commits, PRs, issues, releases, the changelog, docs and code comments.

- **The owner's voice:** plain, minimal, simple, as if the owner wrote it.
- **No "I", "we" or "the user"**, and nothing about who asked for what or how the work was done.
- **No credits:** never mention AI, assistants or agents, and no `Co-Authored-By` or "Generated with" lines.
- **The change and why it matters to the code.** Nothing about private conversations or plans.
- **Short sentences** in everyday words; numbers and names exactly as in the code.

## Shapes

- **Commit:** a short subject line in the imperative or as a noun phrase ("Speed Raid: a run that started is never skipped as used"), a blank line, then a few lines on what changed and why. `Closes #N` at the end.
- **PR:**
  - **What changed:** a bullet list.
  - **Why:** one or two sentences, with a link to the decision or task.
  - `Closes #N`.
- **Changelog:** one line per change under `## Unreleased`, in the [Keep a Changelog](https://keepachangelog.com) spirit.
- **Release notes:** generated from PR labels, then read once and tidied.
