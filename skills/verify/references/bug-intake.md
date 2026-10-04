# verify: something is reported broken

A bug fix goes a short way — reproduce, a test that fails, the fix — while a new
feature goes through planning and the user's decision. Calling a new feature a bug
slips it past both, and the scope grows unnoticed. So the report is sorted first,
and the product spec is what sorts it: **is there a line in the spec, `plexus/spec/`, that
this behaviour breaks?**

## 1. Which case it is

| case | how to tell | what follows |
|---|---|---|
| **A small edit** | a typo or a wording in text a person reads — output, a label, the README — that no program relies on | fix it now: the edit, `test`, a commit; no task, no iteration |
| **Breaks a feature or a constraint** | a line of the spec says otherwise | a bug task, `breaks: [feature-NN]` or `[constraint-NN]` |
| **Undescribed, but plainly broken** | it crashes, loses data, hangs or prints garbage — wrong for any product, spec or not | a bug task; and offer to write the expected behaviour into the feature's text, so it is pinned from now on |
| **Works as described, the user wants otherwise** | the spec says exactly what it does | not a bug: the feature's text changes with the user's agreement, and the work goes through `[stage5]plan` |
| **Undescribed and breaks nothing** | no line covers it, nothing fails | a missing feature: an idea in the backlog, or a short `[stage2]discover` |

A typo in something a program reads — a JSON field, an option name — is **not** a small
edit: someone may already rely on the misspelling, and the fix can break them. It is a
bug against the feature that defines that output, and the user is asked whether the old
spelling must keep working.

An obvious case is taken in at once. A doubtful one — the line between "wants otherwise"
and "missing", or whether a behaviour was implied — is asked, showing what the spec says:

```
"The tool does not show 3xx paths" — the spec says nothing about it.
● A missing feature — to the backlog (Recommended)
○ A bug — it was implied; we write it into the feature's text and fix it
○ Works as intended — nothing to do
```

## 2. Reproduce — before looking for the cause

A fix for a bug that was never reproduced cannot be checked: "it seems fixed" is a
coincidence. Get to minimal steps; every step thrown away is a discarded theory. Not
reproduced → no task yet: record what is known — environment, version, what was done,
what was seen — under "Blocked" in `state.md`, and say what is missing. Often it is one
question for the user.

## 3. The bug task

`plexus/tasks/NN-MM-<slug>.md` with `type: bug`, `breaks`, and `severity` set by
consequences, not by irritation: `critical` — data is lost, the product does not start,
or there is a security hole; `major` — a feature does not work but there is a workaround;
`minor` — it is inconvenient. The Bug section is filled in: what happens, what the line in
`breaks` says should happen, the reproduction. Its Notes give the implementing agent the
order, which is literal:

1. Write the regression test. No fix yet.
2. Run it — **the failure is shown**, not recounted. A test that never failed catches
   nothing: it may check the wrong thing or pass on any code.
3. Find the cause by debugging — logs, bisecting the history, narrowing the input — not
   by reasoning about how the code probably works. A real cause explains the observed
   behaviour in full, including the details that looked like noise.
4. Fix the cause. Run the test — it passes.

Where `config.md` checks that layer by running, `run` captures the result before and
after instead. An edit that removed the symptom without explaining it is written into the
task as exactly that — "symptom removed, cause unknown" — so the next occurrence can be
connected to this one. A bug that grew out of a feature that could be read two ways fixes
the feature's text too, or it comes back.

## 4. Where the task goes

In the current iteration if one is open. Otherwise under the next iteration's number,
with no iteration file yet: planning takes the tasks already filed under its number first.
A `critical` bug in a version already shipped, while another iteration is open, is offered
as a **hotfix**: an iteration of that one task, branched from the release tag and released
on its own — the user's word waives release's rule about an open iteration.

## Handover

```
Bug taken in: task-04-06 · export drops rows with an empty date   critical · breaks feature-08

Reproduced: 3 steps, every time
Placed:     iteration-04, still open
```

Options: **Fix now** — `[stage6]implement` runs task-04-06; **leave it in the iteration's
queue**; **Stop**.
