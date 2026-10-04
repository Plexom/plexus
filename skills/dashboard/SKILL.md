---
name: dashboard
description: In a project with plexus/: builds the progress page - one HTML file from plexus/ and the git history - showing what the product can already do, what is under way and what waits. Use when the user wants to see progress or prepare a summary for someone outside.
context: fork
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *)
---

# Dashboard

Runs in a separate context (`context: fork`): the build reads all of `plexus/` and the git
history and hands back a few lines, so the main session keeps its window for the work.

The page shows the project to someone who does not live in it, built from the same files
the work runs on — no separate bookkeeping to drift from reality. Finished work is shown as
**what the product can now do** — its features — rather than as closed tasks: "6 of 9
promised things work" tells an outsider something, "23 tasks closed" does not. Accepted
iterations are one line each with what they delivered; their tasks are folded inside.

## Building

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dashboard.py" plexus/dashboard.html
```

From the project root.

## Check what came out

The script can finish and still produce nonsense. So:

1. **Exit code.** `0` — everything was read. `2` — some files could not be parsed and are
   named: the page is built, every number on it is an undercount, and the fix belongs in
   those files. `1` — no `plexus/` here.
2. **Open the page** and see that the numbers are there and plausible.
3. **Cross-check one number** against the tables — `python3
   "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" features` — since an intact but wrong header
   passes the exit code.

A section that is absent means nothing was recorded there yet, not that something broke.
"No features recorded" means the spec has none to count from.

## When

Before a conversation with someone outside, after an iteration is accepted, after a
version ships — not after every task: the value is in the snapshot. The page carries the
time it was built, to the minute, so a morning's snapshot never passes for a fresh one. It
is in `.gitignore`; whoever wants it versioned removes that line.

## Report

Two or three lines back to the main session: where the page is, the MVP count, anything the
build could not read.
