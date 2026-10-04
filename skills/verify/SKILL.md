---
name: verify
description: In a project with plexus/: verifies a finished iteration - full tests, the running product, a two-axis review, every delivered feature and constraint, the readiness checklist - and brings it to the user's acceptance; given something broken, takes it in as a bug. Use when an iteration's tasks are done or something is reported broken.
argument-hint: [what is broken, in one line — only when reporting a problem]
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/secrets.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" *) Skill(plexus:review) Skill(plexus:implement) Skill(plexus:plan) Skill(plexus:dashboard) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# [stage7]verify

A file this stage writes that does not exist yet is created from its template, in the
document's language — the templates, printed here so they need not be read:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" task backlog changelog 2>&1
```

Two ways in:

- **No argument** — verify the current iteration once its tasks are closed.
- **A description of something broken** — read
  `${CLAUDE_PLUGIN_ROOT}/skills/verify/references/bug-intake.md` and follow it. It is
  kept apart because an ordinary verification never needs it.

Tests already ran inside every task. This stage checks what no single task could see:
the tasks working together, the product running, and whether this is what the user wanted.

## 1. Preconditions

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" 2>&1
```

Check in order and stop at the first that fails, naming it:

| check | why |
|---|---|
| No task of the iteration is open in the table above — each is `done`, or `wontfix` with a reason | verifying half an iteration accepts what does not exist yet |
| The iteration's work is committed — if not, offer to commit it by the commit rule | the review compares commits; uncommitted work is invisible to it and comes back as "no findings" |
| The iteration's diff against its `base` is non-empty | an empty diff must break here, not inside two parallel reviews |
| Changes no task accounts for are named, and the user said whether they belong | otherwise the review reports the user's own edits as work nobody asked for |

Move the iteration to `verify`.

## 2. The checks through the roles

- `test` — the whole suite, not the subsets the tasks ran.
- `run` — **look at the result**: the output, the response, the window — an interface by
  the rule on screenshots in `CLAUDE.md`. Code that compiled still means nothing.

Do not declare a check passed without having performed it.

## 3. Review

Call `/plexus:review` with the iteration's base as the baseline. It runs two axes in
separate agents: the repository's standards, and whether the code does what the
iteration's features say — by their text as it reads today — without breaking a
constraint and without extra work nobody asked for.

## 4. The readiness checklist

Seven items, all about the product. Walk them one at a time:

1. **It works** — seen running, by you or by the user; not merely compiled.
2. **The iteration's features** — each one in `delivers`, against its **current** text in
   the spec, named separately. A feature reworded since planning is checked as it reads now.
   Where `plexus/design.md` gives it screens, each one as designed: its states, the tokens,
   the motion — against the mockup, seen running.
3. **The constraints** — every one on the spec's front page, on every iteration: any change can break
   any of them.
4. **The iteration's own criteria**, if it has any.
5. **Tests** — the whole suite passes; what can be checked automatically is.
6. **The user's data survives** — what they already have still opens and still works;
   not applicable if the product keeps nothing.
7. **No secrets** — no key, certificate, credential or environment file in the
   iteration's commits. Checked by the script, not by reading the diff — a token in a long
   diff is what reading skims past:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/secrets.py" diff <the iteration's base>`.
   Exit `2` lists what looks like a secret, masked: show each to the user — a test's fake
   key is theirs to call harmless; a real one is removed from the history and revoked, not
   merely deleted in a new commit.

Each item moves on only with one of four outcomes:

| outcome | when | what to record |
|---|---|---|
| checked | you performed the check | how exactly |
| checked by a human | you could not, the user could | who checked, what it showed |
| deferred as debt | neither of you can now | the reason and date in `backlog.md`, "Debt" — only with the user's explicit agreement |
| not applicable | the item means nothing for this iteration | why |

**Before calling an item uncheckable, ask the user whether they can check it**: look at it,
walk the scenario by hand, connect the device. Your not having hands is not the same as a
check being impossible.

## 5. Sort what was found

| finding | where it goes |
|---|---|
| A defect in this iteration's work | a bug task in this iteration (see the reference file for its shape), the iteration back to `in-progress`, back to `[stage6]implement` |
| A defect older than this iteration | a bug task under the next iteration's number, unless it blocks accepting this one |
| Arguable — depends on intent | shown to the user: a task, debt, or nothing |
| Evidence against a decision or a feature | the rule on evidence in `CLAUDE.md`; a demonstrated failure blocks acceptance until it is settled, and if its revision is postponed, a bug task is filed with its severity |
| The criteria are met, but the user meant otherwise | within the iteration's problem: the feature's text is rewritten with them and a task added here; beyond it: an idea in the backlog |

The list is not padded, as in the review's report; nothing found is a normal outcome — say
so.

## 6. Acceptance

Nothing goes back → **show the result to the user**, then ask: accept, or send something
back. The checks are yours; they do not answer "is this what you wanted" — only the user does.

Once they agree:

- the iteration `accepted`, `closed` today — its features count as done from now on by
  themselves; nothing is ticked in the spec;
- a line per user-visible change under "Unreleased" in `plexus/changelog.md`, fixed bugs
  included, written for someone who did not build the product. With `versions: on` in
  `config.md` and no version section in the changelog yet, this is the first working
  prototype: its lines go into a section `## 0.1.0 — <today>` instead, and the handover
  says it — "the product now has its first version number: 0.1.0". Afterwards the number
  moves only at a release;
- debt and ideas that surfaced into `plexus/backlog.md`; the backlog lines the iteration
  `closes` removed from it;
- `state.md` rewritten; a commit by the commit rule;
- then, with `delivery: pull-request`, read
  `${CLAUDE_PLUGIN_ROOT}/skills/verify/references/pull-request.md` and follow it: the push,
  the pull request, its checks.

## 7. Is it time to release

The moment suits when: "Unreleased" has lines a user would notice; the `release` role is
in `config.md` and was checked by running; no open bug task is `critical`; no other
iteration is open. Then one line on why, and the option to release. Otherwise do not bring
it up; if asked, name what is missing. **The release itself happens only on the user's command.**

## Signs that you are cutting corners

- A check reported as passed that you did not run.
- A feature checked against the plan's wording instead of its current text.
- A constraint skipped because "this iteration did not touch it".
- An item closed as uncheckable without asking the user.
- Accepted on the checklist alone, without showing the user the result.

## Handover

Something goes back:

```
[stage7]verify: iteration-04 goes back — 1 defect.

Checks:    41 tests green; the window opens and keeps its layout
Review:    how it is written — 1 arguable; does what was asked — yes, nothing extra
Found:     task-04-05 · the list loses its scroll position on resize   major · breaks feature-07
Checklist: 5 checked, 1 by you, 1 not applicable
```

Options: **Fix** — `[stage6]implement` runs task-04-05; **the arguable finding first**;
**Stop**.

Accepted:

```
[stage7]verify: iteration-04 accepted.

Version:   1.2.0 — unchanged until the next release
Now done:  feature-07 · the list keeps its place, feature-08 · export to CSV
Changelog: 3 lines under Unreleased
Release:   the moment suits — 3 visible changes, release role checked, no critical bugs
```

Options: **Release** — `/plexus:release`, the user types it; **Plan the next iteration** —
`[stage5]plan`; **Look at it from outside** —
`/plexus:dashboard`; **Stop**.
