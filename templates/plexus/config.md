---
stack: <language and platform, or empty until discovery chooses it>
research: on             # on | private | off — may discovery send agents into the outside world; private: queries name the technology, never the product
parallel: not checked    # allowed | not allowed | not checked — can tasks run at once in separate copies
attribution: on          # on | off — the line `Built-with: Plexus` at the end of commits; off where the project's rules say so
delivery: local          # local | pull-request — how an accepted iteration reaches the main branch
versions: off            # on | off — does the product carry version numbers; on: the first accepted iteration is 0.1.0, each release moves it on
---

# Configuration

<!-- template:
How this project is built, run, checked and shipped, and how the agents work on
it. The stages call **roles**, never concrete commands — that is what keeps them
independent of the stack. Values that belong to a person rather than the project —
how many agents at once, whether they want tasks in parallel, screenshots — live
in their personal file, `~/.claude/plexus/defaults.md`, not here.
-->

## External research

<One line on why it is on or off.>

## Roles

<!-- template:
Each role is a command and a promise about what it returns. A role is written here
only after it was run — on a working input and on a deliberately broken one.
-->

| role | command | returns |
|---|---|---|
| `build` | `<command>` | readable build errors |
| `run` | `<command>` | <output / service response / a screenshot of the app window> |
| `test` | `<command>` | what passed, what failed |
| `release` | `<command, or "not used — reason">` | a release artefact |
| `ci` | `<where the remote's checks are defined, or "none">` | what the remote runs on a pull request |

## Testing discipline

<What is covered by automated tests and what is checked by running.>

## Parallel tasks

<Why `parallel` has its value: what was checked, or what shared resource could not
be separated.>

## Manual steps

<What only a human can do — certificates, access grants, vendor consoles — and the
helper script in `plexus/scripts/` that walks through it.>

## Secrets for release

<!-- template:
Credentials live in the system keychain, never in the repository. What the build
and the release need:
-->

- <name> — <where it is stored> — <who issues it>
