---
name: release
description: Ships a version through the release role in plexus/config.md - checks the preconditions, assembles the changelog, calls the role, and makes sure the artefact really was created, is non-empty and carries the right version. Checks separately that no secrets leaked; tags only on an explicit request. Runs only on the user's command - verification says when the moment suits. Use when the user asks to cut a release or build something for people.
argument-hint: [version number]
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/secrets.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" *) Skill(plexus:dashboard) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# [stage8]release

The only stage whose result outsiders see. So what is checked here is not that a command
ran, but that an artefact came out which can be handed over without embarrassment.

**It runs only on the user's command**: a version that has gone out cannot be taken back.
Called at a moment that does not suit, the stage names what is missing — it neither refuses
silently nor ships anyway. A product may be internal and shipped nowhere: then `release` in
`plexus/config.md` says "not used" with its reason, and that is legitimate.

## 1. Preconditions — all of them, named at once

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" git tasks decisions 2>&1
```

The changelog's template, for a project that has none yet:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" changelog 2>&1
```

| check | kind | why |
|---|---|---|
| `release` is in `config.md`, not marked unused, and was checked by running | hard | otherwise there is nothing to ship with, or it fails exactly when relied on |
| No open bug task is `critical` | hard | shipping known data loss is not allowed |
| The working tree is clean | hard | otherwise nobody knows what went into the artefact |
| No iteration is `in-progress` or in `verify` | soft | unaccepted work in a build is a bug nobody knows about yet |
| With `delivery: pull-request`, every accepted iteration's pull request is merged | soft | a release is built from the main branch; work still waiting in a pull request is not in it |

A hard precondition is never waived. A soft one only by the user's explicit word — "ship
without that iteration's work" — never by your judgement. A decision in question does not
block by itself: a demonstrated failure behind it already has its bug task, and a doubt
without a failure is named in the report.

## 2. What goes into the version

Show "Unreleased" from `plexus/changelog.md` and ask for the version number with
`AskUserQuestion`: the one you propose first, the other honest bumps after it. The current
version is the changelog's newest version section; with none, the proposal is `0.1.0`, and
`versions` in `config.md` becomes `on` — a product that has shipped a number has numbers. Propose, do
not choose: a new major number is a promise to users, and it is the owner's to make.

"Unreleased" empty while there are commits since the last release is a discrepancy, not a
detail: iterations were accepted without changelog lines. Assemble the difference from the
history and **show it for confirmation**. Lines are for someone who did not build the
product: "refactored the storage layer" tells them nothing, "the list no longer resets when
the network drops" does.

## 3. Calling the role

One line on what is about to happen and how long it takes — silence in the middle of the
longest operation in the cycle is the worst outcome. Then call `release` from `config.md`:
the role, not a command of your own.

## 4. Check the artefact, not the exit code

**A zero exit code does not mean the artefact exists.** An exit code taken from an output
filter, a file created empty, an artefact left over from the previous build counted as new
— each passes with exit code zero. So the file:

- **exists** at the declared path;
- is **non-empty** and of a plausible size — an application of two hundred kilobytes has the
  wrong thing inside;
- was **created just now** — its time after the build started;
- is **of the promised type** — the archive unpacks, the package installs, the binary starts;
- carries **the version being shipped** inside, not the previous one.

If it does not add up, the release did not happen. Say so plainly: "it built, but I could
not verify it" is a failure, not a caveat.

## 5. Secrets — before anything goes out

No keys, certificates, credentials or environment files in the artefact, nor in the
version's commits — checked by the script, on both:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/secrets.py" path <the artefact>
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/secrets.py" diff <the previous version's tag or first commit>
```

Exit `2` lists what looks like a secret, masked, and exit `1` what could not be looked into —
an archive it cannot open, a file too large; each is shown to the user, and the release
waits until every one is settled. What the build needs is in the system keychain and listed in
`config.md`. A secret that reaches a published artefact is revoked, not deleted: it is
compromised from the moment of publication — which is why this comes before, not after.

## 6. Changelog, state, commit, tag

- "Unreleased" becomes a version section with a date, and "Unreleased" is left empty.
- A public changelog of the project's own at its root is offered as a **separate** step:
  its format belongs to the project.
- `state.md` rewritten; a commit of what this stage changed, by the commit rule.
- **A tag and a push only on an explicit request**, the tag on that commit: agreement to a
  commit is not agreement to a tag, and a tag takes the version outside as surely as a push.

## Report

```
[stage8]release: version 0.3.0 shipped.

Artefact:  dist/app-0.3.0.tar.gz, 4.2 MB, unpacks, version inside matches
Included:  3 iterations, 2 fixed bugs
Secrets:   checked — artefact and commits are clean
In question: decision-05 · plain files — since 2026-10-02, no failure shown
Tag:       not set — waiting on your word
```

Then one `AskUserQuestion`, recommended first: **tag and push**; **rebuild the progress
page** — a shipped version is exactly when outsiders ask; **stop**.
