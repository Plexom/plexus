---
name: implement
description: In a project with plexus/: runs a planned iteration's tasks, each in its own subagent with a context built from the task's ids, and checks every result before it is committed. Use when an iteration is planned, or to continue one.
argument-hint: [iteration, e.g. iteration-02]
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" *) Skill(plexus:verify) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# [stage6]implement

A file this stage writes that does not exist yet is created from its template, in the
document's language — the templates, printed here so they need not be read:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" task backlog 2>&1
```

Runs the iteration's tasks: one agent per task. You conduct; the agents write. **Why an
agent per task:** every task starts in a clean context, and this session carries one
report per task instead of the whole of the work. **Why never two in one tree:** they
overwrite each other's edits and neither sees it happen. The iteration is not accepted
here — that takes verification and the user's word.

## 0. Picking up

The state and the open tasks, substituted before your first move:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" state git tasks decisions 2>&1
```

Take statuses, blockers and decisions from these tables, not from the files: open only
the task you are about to work on. After a task closes, run the tables again —
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" tasks` — rather than reopening files.

If a task is `in-progress`, **continue it, do not start another**. If `git status` shows
changes no task accounts for — the user's own edits — name them and ask whether they
belong to this iteration: unclaimed, they reach the review as work nobody asked for.

Read `plexus/config.md`. If `build`, `run` or `test` is still an unfilled outline, stop:
there would be nothing to check an agent's work with, and `[stage4]setup` comes first.
Read the iteration — its criteria and its out-of-scope list.

On the first task: the iteration to `in-progress`, and the current commit into its `base` —
verification compares against it. A branch only when the header names one (`delivery:
pull-request`): created in one line; with the previous iteration's pull request not merged
yet, ask: branch from it (recommended when this work builds on it — the two merge in order)
or from the main branch.

## 1. Pick the task

The first `todo` task in the table with nothing under "waits for". If `todo` tasks remain
and every one waits, the links are circular, or a blocker is `wontfix` or `missing`, or a
decision is in question: name it and stop.

**Parallel** — only if `config.md` says `parallel: allowed` and the user's personal file
says `tasks: parallel`: then every task with nothing to wait for and no file in common
with another, each in its own git worktree. A file you cannot rule out counts as common.

Move the task to `in-progress` and write it into `state.md`.

## 2. Build the agent's context

The agent did not hear the conversation and cannot ask the user. It gets a **constructed**
context, picked by the ids in the task's header, never a retelling of the session:

- the task file in full;
- the text of each feature it works on, from its part of the spec — the features table
  names the part;
- **every** constraint on the spec's front page — they are few and cheap, and filtering them by
  guess is how one gets broken: "standard library only" looks irrelevant to parsing dates
  until an agent pulls in a date library;
- the terms it will touch, with their identifiers, verbatim;
- each component named in the task, its row from `plexus/architecture.md` with the links
  that touch it and the outside systems it reaches — the code stays inside its component and
  crosses to another only by a link on the map;
- each screen named in the task, its row from `plexus/design.md`, with the whole "Visual
  language" section and the mockup's path — the code uses those token names and values,
  never a colour or a duration of its own;
- `build`, `run`, `test` and the testing discipline from `config.md`;
- each decision named in the task, in full;
- the iteration's own criteria and its out-of-scope list.

Check the task against the decisions table first: a decision it plainly touches but does
not name goes into its header and its context — planning's omission must not reach the code.

And these instructions, in so many words:

- write the code and the tests the task names; run `build` and `test`;
- report in this shape and nothing more: `Done` — one line; `Files` — the changed paths;
  `Build` and `Test` — the command, the counts, the last lines **as printed**; the full log
  only if something failed, saved to a file whose path is given; `Criteria` — each met or
  not; `Conflicts` — anything in a feature or a decision that the work showed to be wrong;
  `Ideas`; `Questions`;
- stay inside the task: anything else noticed goes into the report, not into the code;
- add no dependency the task does not name: one it turns out to need is a question,
  returned — the rule on dependencies in `CLAUDE.md`;
- **return a question rather than guess** when the task leaves open something that changes
  what gets built; **return a conflict rather than work around it** when a feature or a
  decision stands in the way;
- if the task turns out not to fit — more than you can hold, or a second piece of logic
  the task does not name — stop and say what did not fit; more files than expected with
  the same small edit in each is not that: list them in `Files`;
- do not commit.

Before launching, say in one line which task and on which model.

## 3. Check what came back — yourself

**An agent's "done" is a report, not a result.** Every mechanism that reported success
without looking at what it produced failed the same way: an exit code taken from a filter,
an empty file, a leftover from an earlier run. So:

1. The diff is **non-empty** and touches what the task named — nothing unrelated, and no
   dependency the task does not name; one it names arrives with its lock file.
2. Run `test` yourself; the result is what you saw. Run `build` too if they could differ.
3. Where the task says what `run` must show, run it and look — an interface by the rule on
   screenshots in `CLAUDE.md`.
4. Mark each criterion. One you cannot confirm is not met.

A check failed → a fresh agent with the task, the diff and the failure as seen; a
couple of lines you fix yourself and say so. The same task failing twice → the user:
something in the task is wrong, not in the typing.

A question from the agent → to the user with `AskUserQuestion`; the answer into the task
file; launch again. A **conflict** → the rule on evidence in `CLAUDE.md`: to the user with
what it says, what was found, what keeping and changing cost. A demonstrated failure is
never offered as "keep".

The task does not fit — the agent says so, or the diff holds logic the task did not name,
or is far beyond its `size` in lines → stop and ask: cut it — the rest goes back to
planning — or finish it knowingly. The number of files alone is never the reason: one
small edit repeated across many files is said in the report — "one edit in 9 places,
1–2 lines each" — and checked like any diff, not stopped.
Return it to `todo` after the answer, not before: rolling back first erases where the
work stopped.

## 4. Close the task

- Status `done`, `closed` today, and in Progress what was done and how it was checked.
- Ideas from the report → `backlog.md`, "Ideas"; a corner cut knowingly → "Debt", with
  its reason; a new permission or a change to a feature is not recorded quietly — it is a
  product decision and goes to the user.
- A commit naming the task id, by the commit rule; a push only on an explicit request.
- `state.md` rewritten — after every task, not once at the end: a break comes in the
  middle, exactly where the record is needed. It must show which task closed, which is
  next, what was sent back. Keep the `<!-- plexus:... -->` anchors on their headings.

Then look at how loaded the session is — `~/.claude/.plexus-context` if it exists — and
act before the next task:

| left | what to do |
|---|---|
| over 50% | continue |
| 40–50% | offer to clear at this task boundary |
| 30–40% | do not start another task; offer to clear |
| under 30% | clear now, at this boundary |

Without that file, clearing is not offered: continue, and check selectively so the window
lasts — the tail of a test run, a sample of images; screenshots weigh most. Clearing
follows the rule in `CLAUDE.md`, with the line telling the user how to come back.

## Parallel tasks

Each agent works in its own worktree and branch. Check each result by step 3 in its own
tree, one at a time, then merge into the iteration's branch in id order and run `test` on
the merged tree: two tasks green apart can fail together. A merge conflict stops the merge
and goes to the user. Only the main session edits `plexus/`. Clearing is allowed while
agents work in their own worktrees — their branches wait — never while one works in the
main tree.

## Handover

When every task is closed:

```
[stage6]implement complete: iteration-02 — 3 tasks done.

Checked:  each task — diff, 27 tests run here, criteria marked
Returned: task-02-02 once — the share was printed without rounding
Recorded: 1 idea, 1 debt line

Next: [stage7]verify — the full checks, the review, then your acceptance
```

Then one `AskUserQuestion`, recommended first: **Verify** — the full checks, the review,
then your acceptance; or **Stop**. Stopped before
the end: say which task and why, then ask what happens next.
