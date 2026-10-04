---
name: checkpoint
description: In a project with plexus/: captures where the work stopped in the middle of a stage, and the unfinished train of thought, in plexus/state.md. Use before a long break, before /clear mid-stage, when debugging drags on, or when the user asks to save progress.
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# Checkpoint

Records what is in neither the code, nor the commits, nor the tasks: the train of thought
in the middle of the work. A commit keeps the result; a checkpoint keeps the path to it and
the dead ends not worth walking again. It takes a minute; skipped, it costs an hour — the
next session starts over on a hypothesis this one already ruled out.

Every stage rewrites `state.md` at its own handover, so this is for stopping **in the
middle** of one:

- before a long break;
- in debugging, when three theories have been checked and none held;
- when the work waits on someone else's decision, for an unknown time;
- before `/clear` in the middle of a stage.

## 1. What changed

Substituted before your first move — no need to read these separately:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" state git tasks 2>&1
```

The difference between what `state.md` says and what is true now is the content of the
checkpoint. Update it; do not restate it from scratch.

## 2. Rewrite the state

`plexus/state.md` is rewritten in full, not appended to: a stale paragraph beside a fresh
one lies more convincingly than an empty section. **About 80 lines at most** — it is read in
full every session. It holds only what is written nowhere else:

| part | what is in it |
|---|---|
| header | `stage`, `next`, `iteration`, `task` — ids in their one form — and `updated`: today |
| Now | what is being done, one paragraph; if interrupted, what exactly is unfinished |
| Unfinished train of thought `<!-- plexus:thinking -->` | the main part — below |
| Blocked `<!-- plexus:blocked -->` | what, and **by what exactly** — "waiting for an answer" without naming whose is useless |
| Next action `<!-- plexus:next-action -->` | one concrete step |
| Also read | only if something beyond the standard reading order is needed now: a failing test's log, the research a debugging session leans on |

What is closed shows in the task table and the history, and the standard reading order is
in the charter — neither is copied here. Keep the three anchors on their headings: the
session brief finds those sections by them, whatever the headings say.

### The train of thought

Three questions, a line each:

- **What was tried** — the attempts, not "looked for the cause".
- **What did not work, and why** — a ruled-out hypothesis is worth more than a confirmed
  one: it spares the next session the same dead end.
- **Which hypothesis is next** — where you were about to look.

Two illustrations of the shape, from different kinds of work. A service: "Tried: a longer
client timeout, no connection pool, the second replica. Did not work: timeout and pool —
the latency is the same, so not the network; the replica answers the same, so not one node.
Next: the query plan — a missing index." An interface: "Tried: a fixed container height,
then computing it from the content. Did not work: with another system font both clip the
last line. Next: measure the text before rendering."

Empty only when the work is finished, not merely stopped — then say exactly that.

## 3. Check that it was written

Re-read `state.md`: `updated` is today's; all three anchors are on their headings; "Next
action" is a concrete step, not "continue the work"; every file under "Also read" exists;
the length is within about 80 lines — `wc -l plexus/state.md`. If not, fix it and read again.

## 4. Before /clear

Updating the state is one of three steps: then `git status`, then commit what is
uncommitted by the commit rule. If committing is not possible now, say so and name what
will be left hanging — clearing silently over uncommitted work is a loss found a session
later. Then tell the user how to come back: "Type /clear, then write anything — we
continue with [the stage and step]."

## Handover

```
State captured.

Recorded: task-04-02 sent back once, two ruled-out hypotheses about the cause
Blocked:  task-04-03 — waiting on access to the test rig
Tree:     clean, last commit 20 minutes ago
```

Then one `AskUserQuestion`, recommended first: **clear the context** — you type `/clear`,
then write anything; **continue** where it stopped; **stop**.
