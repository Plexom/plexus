---
name: update
description: Brings a project running on Plexus up to the installed plugin version - replaces the charter block in CLAUDE.md, carrying over the commit rule and any rules the user had recorded inside the block. Shows the whole plan before touching anything. Use when the session brief says the plugin is newer than the charter, or when the user asks to update Plexus in this project.
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ground.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/charter.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# Update

Moves a project to the Plexus version that is installed now. The charter block in
`CLAUDE.md` is a copy made at initialization, and nothing refreshes it by itself: a project
left on an old charter runs the new stages by the old rules. **Nothing of the project's is
lost** — the block is Plexus's, what the user put into it is theirs, and so is every line
of `plexus/`.

## 1. Where the project stands

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ground.py" 2>&1
```

The charter's version is in the `CLAUDE.md` line, the installed one in `Plugin`.

- No Plexus block or no `plexus/` — this is not an update: `/plexus:init` brings Plexus in.
- Broken markers — the block cannot be replaced safely; name the lines and stop.
- The versions match — say so in one line and stop.
- **The major number differs** — the layout of `plexus/` changed between them, and moving
  it is not supported by this version yet. Say so plainly and stop, touching nothing:
  a half-moved state is worse than an old one.
- The working tree is not clean — offer to commit first: the update should be one commit
  of its own, readable apart from anything else.

## 2. What carries over

What the old block holds that matters — its version, the commit rule, and every rule the
installed template does not have — read by the script, not by eye:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/charter.py" --old 2>&1
```

| from the old block | goes to |
|---|---|
| the **Commits** rule, with its quoted original | `{{COMMIT_RULE}}` |
| a rule Plexus itself retired — the script names them | dropped; said in one line |
| any other rule the current template does not have | asked about, below |
| everything else | replaced by the template |

A rule present in the old block and absent from the template is either one Plexus has
since dropped or merged, or one the user recorded inside the block. They cannot be told
apart for certain — so ask. A rule followed by a quoted original is almost certainly the
user's: recommend keeping it. Keeping means moving it **below the block**, outside the
markers — inside, the next update would overwrite it. A value hidden in such a rule goes
where it belongs: the project's into `plexus/config.md`, the person's into
`~/.claude/plexus/defaults.md`.

## 3. Show the plan, then act

```
Update: Plexus 1.0.0 → 1.1.0

Charter:     replaced; commit rule carried over
Your rules:  1 kept, moved below the block — "run the linter before each commit"
```

Then one `AskUserQuestion`: apply as shown (recommended); change what is kept — a follow-up
with `multiSelect` over the rules in question; cancel.

Then the charter, in one call — the rules chosen to keep go under `below`, word for word
with their quoted originals, and a value hidden in one goes to its file first:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/charter.py" . <<'PLEXUS'
=== commit rule
…
=== below
…
PLEXUS
```

It replaces the block where it stands, puts the kept rules right below it, checks one
block, the new version, no `{{`, every kept line below it and everything outside as it was
— or puts the file back. Exit code `1` — nothing changed; the reason is printed. Do not
edit the block by hand. Then the session brief reads the project — run it and look:
`echo '{}' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/session_brief.py" SessionStart`

## Handover

```
Plexus updated to 1.1.0.

Charter:  replaced; 1 rule of yours below it
Checked:  markers, placeholders, the session brief reads the project
```

Then one `AskUserQuestion`, with the commit offered by the commit rule: **continue** — the
next step from `state.md`; or **stop**.
