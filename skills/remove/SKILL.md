---
name: remove
description: Takes Plexus out of a project cleanly - shows everything it left there, asks what to do with the project's data in plexus/, removes the charter block from CLAUDE.md and its own lines from .gitignore, asks about unmerged iteration branches, and does it all in one revertable commit; then says how to switch the plugin off for this project or everywhere. Use when the user wants to stop using Plexus in a project.
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ground.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/undeploy.py" *)
---

# Remove

Takes Plexus out of this project without leaving debris and without losing anything that
belongs to the project. Plexus put its things in marked places precisely so they can be
found again: the charter between `<!-- plexus:begin -->` and `<!-- plexus:end -->` in
`CLAUDE.md`, its `.gitignore` lines between `# plexus:begin` and `# plexus:end`, the state
in `plexus/`. Only what it put there is taken back.

**The data is the project's, not the plugin's.** `plexus/` holds the product's
specification, its decisions and the history of the work — useful without Plexus. It is
never deleted without asking.

## 1. What Plexus left here

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ground.py" 2>&1
```

- No `plexus/`, no block and no `.gitignore` lines — Plexus is not in this project; say so
  and stop.
- Broken markers in `CLAUDE.md` — what is Plexus's cannot be told from what is the user's,
  and the removal refuses them: name the lines, show where the pair is broken, and settle
  with the user which lines are the charter — fixed, committed, then go on.
- The working tree is not clean — offer to commit first: the removal must be one commit of
  its own, so one revert brings everything back.
- A `plexus/` directory but no markers anywhere — a project deployed by hand or damaged:
  say what was found and ask before going on.

Show it to the user as a table — what, where, what happens to it — before touching
anything.

## 2. Ask

One `AskUserQuestion` call, recommended first:

- **The data in `plexus/`**:
  - keep it as plain documents (recommended) — the directory is renamed to
    `docs/plexus-archive/`. It has to be renamed: while a directory called `plexus/`
    exists, an installed Plexus keeps briefing every session about it;
  - delete it — it stays in the git history;
  - keep it where it is — only if the plugin will be switched off for this project,
    which the last step does.
- **Unmerged iteration branches**, if there are any: leave them, merge them, or delete
  them. Never delete a branch silently: it may hold the only copy of unfinished work.
- **Confirmation** of the whole plan.

## 3. Take it out — one call

Branches first, as the user chose — each by its own command, since a deleted branch may
hold the only copy of unfinished work. Then everything else in one call:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/undeploy.py" . --data=archive   # or delete, or keep
```

It cuts the block out of `CLAUDE.md` — deleting the file when nothing else was in it —
and the marked lines out of `.gitignore`, leaving every other line byte for byte, the
secret patterns above all; moves, deletes or keeps `plexus/`; checks the result; and
commits it all as "Remove Plexus", or puts everything back. Do not edit these files by
hand, before or after: its checks and its way back cover only what it did.

Exit code `1` — nothing changed; the reason is printed: a tree that is not clean, broken
markers, an archive already in place. Exit code `2` — removed, but git could not commit:
say what git said, and after the fix commit the paths it names. Then check that the session
brief is silent here:
`echo '{}' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_brief.py" SessionStart` prints
nothing. A push only on an explicit request.

## 4. The plugin itself

Removing Plexus from the project does not uninstall the plugin; that is the user's command,
and there are two:

```bash
claude plugin disable plexus@plexus --scope local
```

switches Plexus off **for this project only**, for this user — it writes
`enabledPlugins` into `.claude/settings.local.json`; other projects keep it.

```bash
claude plugin uninstall plexus@plexus
```

removes it everywhere. Only then is the personal file, `~/.claude/plexus/defaults.md`,
worth mentioning: it belongs to the person, not to this project — offer to delete it, and
leave it if they would rather keep it for later.

In this project, if `.claude/settings.local.json` holds `Edit(./plexus/**)` — the rule init
offers — offer to take it out with the Edit tool, touching nothing else in that file; with
`plexus/` gone it has nothing left to cover, and it is harmless if kept.

## Report

```
Plexus removed from this project.

Data:      plexus/ → docs/plexus-archive/ (product, 4 decisions, 3 iterations)
Charter:   removed from CLAUDE.md; your 2 rules below it kept
.gitignore: plexus lines removed; secret patterns kept
Branches:  iteration/03-export left as it is
Commit:    "Remove Plexus" — one revert brings it all back

To switch the plugin off here: claude plugin disable plexus@plexus --scope local
```
