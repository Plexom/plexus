---
name: setup
description: In a project with plexus/: fills plexus/config.md with the build, run, test and release roles and checks each by running it, on a working and a deliberately broken input; checks whether tasks can run in parallel. Use once the stack is chosen, or when the build changed.
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *) Skill(plexus:plan) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# [stage4]setup

Teaches the framework to work with this project's stack. The stages call roles, not
commands — which is why a configuration set up once keeps every other stage
independent of the stack.

## 1. The stack

Read `plexus/config.md` — its `stack`, and the commands `init` found if the project had
code: those are not searched for again, they are checked. Then the decision about the
stack:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" decisions 2>&1
```

Look at the project itself: manifests, build files, CI.

**Before the first command runs, say what running means.** A build or a test run executes
the project's code; installing its dependencies downloads packages and runs their install
scripts. In a project that had code before Plexus — someone's, perhaps a clone — show the
commands about to run, as found, one line each, the installs among them with what they
fetch, and ask once with `AskUserQuestion`: run them (recommended when the user wrote or
trusts this code), or show each before it runs. A fresh skeleton names the packages it
installs in the same way.

If the stack has not been chosen,
this is not setup's job: say that discovery chooses it together with the architecture,
offer `[stage2]discover`, and stop.

If there is no code yet, create **the smallest skeleton the stack allows** — one entry
point and one test — so every role has something to run and something to break on
purpose. A role checked against an empty directory has been checked on paper. The
skeleton is the only code this stage writes.

## 2. The four roles

| role | must | returns |
|---|---|---|
| `build` | build the project | readable errors — pipe a verbose log through a filter, since an unfiltered log eats context faster than it helps |
| `run` | run it and show the result | output for a console, a response for a service, a screenshot of the app window for an interface — **without it the agent writes blind** |
| `test` | run the automated tests | what passed, what failed |
| `release` | ship a version | an artefact ready to reach people — or "not used", with the reason |

**Run every command before writing it down.** A role that exists only on paper is worse
than a missing one: people will rely on it. **Check each on failure too**: a role must
tell "done" from "did not work" by its exit code. The usual ways of lying — the exit
code taken from the output filter, a file created but empty, a process that starts and
dies — show only on a deliberately broken input: broken code, an unreachable path.

## 3. Screenshots — only with the user's permission

Only for a product with an interface — a window, a web page, a mobile screen. A utility,
a service or a library returns text, and there is nothing to ask. Init usually asked it
already: `screenshots` in `~/.claude/plexus/defaults.md` saying `allowed` or `not allowed`
is the user's standing answer, and nothing is asked again. With `ask`, nothing set or no
file, ask with `AskUserQuestion`, explaining:

- **why** — without screenshots the interface is checked blind: the code built, but
  nobody saw what is on the screen;
- **what** — only the application's window, never the whole screen, so other windows,
  messages and terminals stay out; if the window cannot be captured on its own, no
  screenshot is taken;
- **when** — after a build, when a task says what must be visible, at acceptance, before
  and after a bug fix;
- **where** — a temporary folder outside the repository, as the rule on screenshots in
  `CLAUDE.md` names it — deleted when the stage ends, never committed;
- **who sees it** — Claude, like any message in the conversation: a window showing
  someone's private data is not captured, it is described by the user instead.

Options: allow — the system's screen-recording permission is granted by the user, you
say where it is but never change security settings yourself; or do not allow — the
interface is then checked through the user, who is asked for a screenshot or asked what
they see. Write the answer to the user's personal file, creating it from
`${CLAUDE_PLUGIN_ROOT}/templates/defaults.md` if it is absent: it is permission to
capture their screen, not a property of the project. `config.md` says only what `run`
captures — which application's window.

## 4. Can tasks run in parallel

Parallel tasks run in separate copies of the project, and everything inside the folder
is separate by nature. What collides is what is shared on the machine: a port, a local
database, shared temporary files, a cache. Check by running: make a second working tree,
run `test` in both **at the same time**, remove the copy.

- Both pass as they do alone → `parallel: allowed`.
- They collide → find why and **offer to separate them**: the port from a variable or a
  free one, a database name and a temporary folder per copy, a cache per copy. Separating
  must not harm the project: only the test and run configuration changes, never the
  product's code; a single ordinary run behaves exactly as before — with no variable set,
  the old port and the old database; the change is shown before it is made and made only
  with the user's agreement, in a commit of its own so it can be reverted; afterwards
  `test` passes alone, as before, and in two copies. Then check again.
- Separating is impossible — one physical device, an outside service with one test
  account, not enough machine — or needs a change to the product's code, or the user
  declines → `parallel: not allowed`, with the reason in one line.

## 5. Testing discipline, manual steps, secrets

- **Testing discipline** — what is covered by automated tests and what is checked by
  running. A guideline: logic and module boundaries by tests; the presentation layer,
  system calls and what depends on the user's environment by `run`, keeping what it
  returned.
- **Manual steps** — what only a human can do in this stack: certificates, access grants,
  a vendor console. Write them up as a helper script in `plexus/scripts/` that walks
  through the steps and checks each: they happen rarely and are forgotten completely.
- **Secrets for release** — what the build and the release need and where each is kept:
  the system keychain, never the repository.

All of it goes into `plexus/config.md`.

## 6. How the work reaches the main branch

Only when the ground has a remote — `git remote -v` names one. Without it, `delivery:
local`: an accepted iteration is merged here, on the user's word, and nothing is asked.

With a remote, ask with `AskUserQuestion`:

- **through a pull request** (recommended when others work in this repository, or the
  remote runs checks) — at acceptance the iteration's branch is pushed and a pull request
  opened, the remote's checks run on it, and it is merged there — by the user or the team,
  as the project merges anything;
- **merged here** (recommended when the user works alone) — as without a remote; pushing
  stays a separate request.

Write the answer as `delivery` in `config.md`; with pull requests each iteration gets its
own branch, which planning names. With pull requests: find what the remote
runs — `.github/workflows/`, `.gitlab-ci.yml`, another CI's file — and record it as the
`ci` role, or `none`; check whether `gh` (or the host's own tool) is installed and signed
in — `gh auth status` — and when it is not, say that pull requests will be opened by a link
instead, one line. Setting up a CI that does not exist is a change to the project's build
the user asks for, not something this stage adds on its own.

## Handover

```
[stage4]setup complete: Python 3.12 command-line tool.

Verified:  build — 3 s, errors readable; test — 12 tests, a broken one reported as failed
           run — prints the summary; release — not used, internal tool
Parallel:  allowed — test ran in two copies at once
Delivery:  pull request to main; CI — .github/workflows/test.yml
Deferred:  nothing

Next: [stage5]plan — the next iteration, cut into tasks
```

Then one `AskUserQuestion`, recommended first: **Plan** — the first iteration, cut into
tasks; or **Stop**. The commit is offered by the commit rule.
