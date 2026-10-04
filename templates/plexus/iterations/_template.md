---
id: iteration-NN
title: <short iteration name>
status: planned          # planned | in-progress | verify | accepted | dropped
delivers: []             # the features this iteration makes work: [feature-01, feature-02]
closes: []               # backlog lines it takes in: [backlog-04]
created: <YYYY-MM-DD>
closed:
base:                    # the commit implementation started from; verify and review compare against it
branch:                  # only with `delivery: pull-request` in config.md: iteration/NN-<slug>
---

# iteration-NN · <Title>

<!-- template:
The iteration refers to the spec in `plexus/spec/` instead of retelling it: what holds for
good is in the text of its features and is checked there, as it reads on the day of
acceptance. Only what is true for this iteration alone is written here.
-->

## The problem

<What does not work for the user today, and for whom. If it cannot be stated, the
iteration was invented rather than found.>

## Out of scope

<What does not belong here even though it suggests itself. This guards against creep.>

## Criteria for this iteration only

<What holds only until this iteration is accepted — data carried over from the
previous format, "CSV only for now". Leave empty if there is nothing of the kind.>

- [ ] <criterion>

## Interface behaviour

<How the interface behaves and why, where this iteration decides it. Behaviour that
stays goes into the feature's text as well.>

## Open questions

<What is not settled. A question about *what* to build blocks planning; one about
*how* does not — it is carried into `state.md` and settled during the work.>
