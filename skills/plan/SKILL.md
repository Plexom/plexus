---
name: plan
description: In a project with plexus/: plans the next iteration - which features of the spec it delivers, cut into tasks that each fit one subagent - and proposes it before writing files. Use when an iteration is due, or the user asks to plan or break work down.
argument-hint: [features or what the iteration should deliver, in one line]
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" *) Skill(plexus:implement) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# [stage5]plan

A file this stage writes that does not exist yet is created from its template, in the
document's language — the templates, printed here so they need not be read:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" iteration task architecture 2>&1
```

Assembles one iteration and its tasks from what has already been decided. **This is not
a second discovery**: if the material is not enough, say what is missing and offer
`[stage2]discover`. One iteration at a time — the next is planned after this one is
accepted, when it is known what this one taught.

**An iteration already open.** If one is `planned` or `in-progress`, this call is a
change of mind about it. Ask: **revise it** — its files are edited in place, done tasks
stay done, removed ones become `wontfix` with the reason, new ones continue the
numbering; or **drop it** — `dropped` with the reason, its open tasks `wontfix`. Nothing
is deleted: the record of what was tried stops it being tried again. The one exception
to a single open iteration is a hotfix — see verification.

## 1. The material

The tables first — what is open, what is in force, what is already filed:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" 2>&1
```

Then the spec: the front page `plexus/spec/index.md` — constraints, terms — and the parts
the iteration's features live in, as the features table names them; `plexus/design.md` if the
product has one, for the screens each feature lives on, `plexus/architecture.md` if the
system has one, for the components the work falls into, and `plexus/backlog.md`. Open a
decision in full when the iteration touches it, and check its "Revisit if" against what
this iteration asks for: an iteration is where a decision most often goes stale. A sign
that has appeared is brought to the user by the rule on evidence in `CLAUDE.md`, before
anything is planned on top of it. Research notes are not read here: their conclusions are
already in the decisions and constraints. Accepted iterations are not reread either —
what they delivered shows in the features table.

Look at the code, if there is any: tasks must name real modules, and the code shows where
a preparatory edit is needed. Speak only in the spec's terms: an iteration
written in other words than the code drifts apart from it within a month.

## 2. The iteration

**What it delivers** — by default the next open features in scope `MVP`, unless the user
named others; debt from the backlog it takes in. Bug tasks already filed under its number
come in first.

The iteration **refers to the product instead of retelling it**. The rule for what goes
where: what holds for good — including edge cases — is in the text of a feature, in
the spec; what holds only until this iteration is accepted — data carried over from
an old format, "CSV only for now" — is in the iteration's own criteria. A feature missing
from the spec or worded too loosely to check is not fixed here: it is a decision, and
it goes to discovery.

Write in the iteration:

- `delivers` — the features; `closes` — the backlog lines;
- **the problem** — what does not work for the user. If it cannot be stated, the
  iteration was invented rather than found;
- **out of scope** — what does not belong here though it suggests itself. The most
  underrated section: it guards against creep better than any estimate;
- **criteria for this iteration only**, if there are any;
- **interface behaviour** this iteration decides, and its reason;
- **open questions** — sorted: not knowing *what* the work is blocks, name it and offer
  discovery; not knowing *how* does not, carry it into `state.md`. Never settle one
  silently for the user.

**One iteration or two** is decided by size: split only when the tasks will not fit one
session's worth of reports and a verification, or when part of the work can reach the
user on its own. "Tidier" is not a reason — every iteration pays for a verification and
an acceptance.

## 3. The tasks

A task is what one subagent carries out from start to finish, in a clean context, with
nobody to ask. So it **fits** — one agent holds it, and the main session checks it in one
pass (see Task size below); it is **self-contained** —
its file says what changes and which part of its features it covers ("the counting here,
the output in task-02-03"), its tests, and in its header the features it works on, the
screens of `plexus/design.md` it builds or changes, the components of
`plexus/architecture.md` it works in, and the decisions it touches; and it **declares what blocks it** — `blocked_by: [task-02-01]` reads
"waits for task-02-01".

**Every task carries its own tests**, written with the code: a defect found at the end is
found where it costs most. Where `config.md` says a layer is checked by running, the task
says what `run` must show.

Cut along behaviour, not along layers: "the storage layer" is a band nobody can check on
its own; "an entry is saved and shows up in the list" is a task. Preparatory edits come
first. **A wide refactor** — one mechanical edit across the codebase — is laid out as
expand (the new form beside the old) → migrate in batches, each a task blocked by the
expansion → contract (the old form removed, blocked by every batch).

Signs of a bad cut: a task that cannot be checked until the next is done; two tasks
editing one file for one behaviour; a task that exists for order rather than a result
("prepare the structure"); every task blocking the next in one chain.

## Task size

**A task is as large as one result is**, and is split only for one of two reasons:

1. **It does not fit** — what the agent must read and write (the code it changes, what
   that code calls, the task, its tests) would fill most of its window, and the end of
   the work is done with the beginning half-forgotten.
2. **It is too hard to check in one pass** — several unrelated judgements in one diff (a
   new algorithm, a new screen and a storage change together), so a check would skim
   instead of read, and a failure would throw away work that was fine.

Anything else is not a reason: every task costs an agent's start, a constructed context
and a check, and "tidier" pays that for nothing. **The number of files is not a measure.**
One edit repeated across the codebase — a rename, a parameter passed through, an import
moved — is one judgement however many files it touches: nine files of one or two lines
each check faster than one file of two hundred.

`size` records how much the check will read, as an estimate:

| `size` | the check reads |
|---|---|
| `S` | one behaviour; up to about a hundred changed lines; a repeated small edit in any number of files |
| `M` | one result across two or three modules, or a new layer; up to about four hundred lines |
| `L` | one result that is large but still one judgement and still fits; say in the plan why it is not split |

As an estimate, not a measurement: past eight tasks, an iteration most likely splits.

## 4. Propose, then write

Before any file, show the iteration and its tasks, every id with its name:

```
iteration-02 · Error share and a time filter
delivers feature-02 · share of 5xx errors, feature-03 · filter by time range
closes   backlog-04 · dates without a time zone

  task-02-01 · the error count is kept per request   S · unblocked
  task-02-02 · the share is printed                  S · waits for task-02-01
  task-02-03 · --from and --to narrow the input       M · unblocked
```

Then ask: approve as shown (recommended), or revise — the features it takes, the cut, a
blocking link that is not a real gate — each option saying what it reopens. A revision
comes back as a new proposal; one approval covers the whole iteration.

A task that brings in a dependency names it in its file, and the proposal shows it with its
licence and size — "adds dependency: date-fns · MIT · 20 KB" — since approving the plan is
the user's decision to take it on.

An iteration that needs a component the map does not have, or a link between two that do
not talk yet, shows it in the proposal — "adds component-05 · notifications, called by
component-02" — and, approved, it goes into `plexus/architecture.md` with the rest. A new
component is architecture: one that is expensive to undo also gets its decision.

Then write `plexus/iterations/NN-<slug>.md` and `plexus/tasks/NN-MM-<slug>.md` from their
templates, tasks numbered in dependency order, and rewrite `state.md`. The spec is not
changed here. `branch` is filled only with `delivery: pull-request`: a person working alone
works on the main branch, a commit per task, and one revert undoes any of them.

## Handover

```
[stage5]plan complete: iteration-02 · Error share and a time filter.

Delivers: 2 features; closes 1 debt line
Tasks:    3 — 2 S, 1 M; task-02-01 and task-02-03 can start now
Open:     how long keys live — does not block, carried into state.md

Next: [stage6]implement — each task in its own agent, checked before it is committed
```

Then one `AskUserQuestion`, recommended first: **Start** — each task in its own agent; or
**Stop**. The commit is offered by the commit rule. Revising is not an option here: the
plan was approved before any file was written; a change of mind is a new `/plexus:plan`.
