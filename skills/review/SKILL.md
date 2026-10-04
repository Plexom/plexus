---
name: review
description: In a project with plexus/: reviews changes in two separate subagents - the repository's standards and decisions, and whether the code does exactly what the iteration's features or the bug task ask. Use when verifying an iteration, or when the user asks for a review of a branch or changes.
argument-hint: [baseline: branch, commit or path]
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *)
---

# Review

A review of the changes along two axes. The axes run **apart**: an agent that has read the
requirements starts seeing in the code what was promised rather than what is written.
Separate contexts are not an optimization but a condition of honesty.

## 1. Fix the baseline

The point of comparison is what the user named, or the iteration's `base` — the commit its
implementation started from, in its header.
**First check that the work is committed**: review compares commits, and changes still in
the working tree are invisible to it — the agents would honestly report "no findings" on
nothing. If the tree is not clean, offer to commit, then launch. Make sure the baseline
resolves and the diff is **non-empty** before launching: an empty diff must break here.

## 2. Find what was asked for

In order: the iteration named by the branch or by `plexus/state.md` — the features it
`delivers`, taken from their parts of the spec **as their text reads now**, every constraint,
its own criteria and its out-of-scope list, and the rows of `plexus/design.md` for the
screens its tasks name; a bug task — the lines it `breaks`; a path the
user handed over. If there is nothing, the second axis honestly reports "nothing to check
against" and does not invent requirements.

## 3. Launch both axes

"Axis", "standards" and "spec" are this skill's own words. Whatever the user reads — the
report, the handover, a question — names each check by what it looks at, in the
conversation's language: **how the code is written** (by this project's rules) and **whether
it does what was asked**, as in «Как написан код» and «Делает ли то, что просили».

Each agent gets a constructed context — the diff, the baseline, its own subject — never a
retelling of this session. **Always two axes, always two agents**, and you conduct
neither: whoever planned or checked the work knows what was meant, while review checks
what is written.

What scales is the depth of each axis, measured by the diff:

| diff | what to send | model |
|---|---|---|
| within one module | the diff and the requirements in full, the axis's subject in one line; no smell list — at this size it is longer than the edit | mid-tier |
| wider, a broad refactor, unfamiliar code | the diff, the baseline, the requirements, the axis's subject in full | expensive |

Where judgement is required, do not economize: "this looks like a problem" is an
interpretation, and a weak model on a large change either stays silent or buries the report
in nitpicks. If the user asks to go cheaper, say what it risks and let them decide.

### The "standards" axis

How things are written in this repository: its documented conventions, the decisions in
force — the table from `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" decisions`,
opening the ones the diff touches — the map in `plexus/architecture.md`, and the terms on
the spec's front page. Code that reaches from one component into another by a way the map
does not show — a direct database read across a boundary, a call nobody drew — is a finding:
either the code is wrong or the map is out of date, and the report says which it looks like. On top of that, a base
set of code smells that applies where nothing is documented, each a flagged guess, never a
violation: `${CLAUDE_PLUGIN_ROOT}/skills/review/references/smells.md` — give its path to
the agent when the axis is sent in full, and do not read it yourself.

A dependency the diff adds that no task names is a finding too: nobody decided to take it on.

Code that contradicts a decision is an ordinary finding: the code is wrong. If instead the
decision itself looks wrong — the change shows a premise does not hold — it is reported
separately, for the rule on evidence in `CLAUDE.md`: never silently "fixed" either way.

### The "spec" axis

Does the code do what was asked. Three questions, the third weighs most:

1. Is every feature in `delivers` actually met — checked, not asserted — and is no
   constraint broken?
2. Was anything asked for forgotten?
3. **Was anything extra done** — something nobody asked for? Unrequested work is not free:
   nobody reviewed it and nobody will maintain it.

## 4. Merge the findings

One report, in descending order of seriousness, split into **confirmed** — reproducible,
visible in the code, with a failure scenario — and **arguable** — depends on intent, the
user decides. Do not pad: twenty remarks jumbled together read as zero. Both axes silent is
a normal outcome — say so.

## Handover

Called from verification, skip this: the findings go back to its sorting step, and two
handovers in a row would ask the user the same thing twice. Called on its own:

```
Review complete.

How it is written:     1 confirmed, 2 arguable
Does what was asked:   features met, no constraint broken; found something extra — a cache nobody asked for
```

Then one `AskUserQuestion`, recommended first: **fix the confirmed ones** — each becomes a
task; **work through the arguable ones**; **accept as is** — recorded as debt with a
reason.
