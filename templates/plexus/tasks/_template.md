---
id: task-NN-MM
iteration: iteration-NN
title: <short task name>
type: feature            # feature | bug | refactor
status: todo             # todo | in-progress | done | wontfix
size: M                  # S | M | L — how much the check reads: S one behaviour, ~100 lines; M 2–3 modules, ~400 lines; L one large result that still fits
feature: []              # the features this task works on: [feature-02]
screens: []              # the screens of plexus/design.md it builds or changes: [screen-01]
components: []           # the components of plexus/architecture.md it works in: [component-02]
decisions: []            # the decisions it touches: [decision-03]
blocked_by: []           # the tasks it waits for: [task-NN-01]
severity: none           # bugs only: critical | major | minor
breaks: []               # bugs only: what the bug violates: [feature-02] or [constraint-01]
created: <YYYY-MM-DD>
closed:
---

# task-NN-MM · <Title>

## What it does

<The change in full, and which part of its features it covers ("counting here,
the output in task-NN-03"). A subagent carries it out with no memory of the
conversation that produced it — write it so that nothing has to be asked.>

## Criteria

- [ ] <a checkable statement, narrower than the feature>

## Tests

<Which automated tests this task adds — or, where `plexus/config.md` says the layer
is checked by running, what the `run` role must show.>

## Bug

<Only for `type: bug`; delete the section otherwise.>

**What happens:** <the observed behaviour>

**What was expected:** <what the feature or constraint in `breaks` says>

**Reproduction:** <the minimal steps>

**Cause:** <found by debugging, not by guesswork>

**Regression test:** <the test, shown failing before the fix>

## Notes

<Known pitfalls, where to look.>

## Progress

<Filled in as the work goes: what is done, what did not work, where it stopped.>
