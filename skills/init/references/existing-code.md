# init: a project with code already written

Bringing Plexus into a living project is the most fragile thing the framework does:
someone else's code must not be touched, and trust is lost at the first unexpected
change. So the plan comes first, and nothing is created until the user agrees.

## 1. The plan — before any change

Print it with the real project name and whatever is visible at a glance, then ask with
`AskUserQuestion`: continue (recommended), change the plan, or cancel.

```
Plexus is about to join <name>. The plan:

1. READ (read-only)
   • structure, languages, how it builds; tests and CI; recent history, README, TODO/FIXME
2. CREATE, touching nothing that exists
   • plexus/ — product, configuration, state, and what the reading finds something for
   • a Plexus block in CLAUDE.md, between markers; lines in .gitignore
3. ASK YOU about what code cannot tell: what the product is for, where it stops
4. NOT DO: change, reformat or rename code; touch dependencies, the build or CI;
   commit anything but Plexus's own files, push at all
```

A refusal leaves no trace: until the answer comes, create nothing, not even a directory.

## 2. Reading

Read-only, by agents with a constructed context each. The areas are independent, so
they run at once:

| Agent | Area | What it brings back |
|---|---|---|
| 1 | Structure and stack | Languages, package manager, entry points, modules, how it builds and runs — the commands, as found |
| 2 | Tests and checks | How they run, what they cover, CI, what counts as passing |
| 3 | History and agreements | Rate of change, decisions stated in the README and commits, TODO and FIXME with their places |
| 4 | What the product does | What a user can do with it, one line each, from the README, `--help`, API routes, screens, test names — each with where it was seen |

Before launching, say who runs on which model and allow a change: reading someone
else's code is comprehension, a mid-tier model is enough; you draw the conclusions when
merging. Afterwards `git status` must be what it was before — if anything changed, say
so plainly and roll it back.

## 3. What the reading gives

Shown before the questions of init's step 2 — what was found, not what is decided — each
line saying where it came from; the rounds then ask only what the code cannot tell:

```
Found in the code:
  Stack         Python 3.12, pytest — from pyproject.toml
  Commands      build/run/test found — [stage4]setup checks them by running
  Commits       small commits straight to main — from the history
Already works (becomes iteration-00):
  feature-01 · top paths by request count      — --help and tests
  feature-02 · share of 5xx errors             — --help and tests
  feature-03 · filter by time range            — only in the code, not in --help
Also:           2 decisions from the README, 5 TODO → debt
```

- **Features** at the level of what a user can do — 5 to 20 lines, the level discovery
  writes new ones at — never a map of functions, which goes stale with every edit. A line
  seen only in the code, or otherwise doubtful, is **asked, not dropped**: a working
  feature, something internal, or unfinished? Often the user knows at once.
- **Terms** that recur in names and mean something in the domain; generic words like
  "service" or "manager" do not belong.
- **Decisions** stated in the README or the history, marked as reconstructed; their
  "Rests on" and "Revisit if" stay empty rather than invented.
- **Debt** from TODO and FIXME, with where each sits.

Do not migrate existing tickets, docs or plans: `plexus/` describes the way forward and
does not rewrite the past.

## 4. What is asked

What code cannot contain — what the product is for and what it deliberately does not do —
is asked in init's step 2, in plain words. The doubtful features go into the same rounds;
commits, if the history is unclear, into step 4. What was confirmed becomes part of the
spec shown in step 3.

## 5. What goes into the deployment beyond the common tail

The same single call, with further sections — `=== iterations/00-before-plexus.md`,
`=== decisions/<file>.md`, `=== backlog.md`, and `=== architecture.md` — the map drawn
from what agent 1 found: the components the code already has, what each owns, how they
call each other, the outside systems, marked as reconstructed; the notice of step 5 names
them too.

- `plexus/spec/` — the purpose on the front page, plainly; a part per area
  the code shows — its modules, screens, API routes, as the user would name them — with
  the confirmed features in it, scope `MVP`; the terms. A large codebase is attached a
  part at a time: the reading covers the areas the user names first, and the rest of the
  front page's list says "not read yet", so the spec never pretends to cover code nobody
  looked at.
- `plexus/iterations/00-before-plexus.md` — from the iteration template: `id: iteration-00`,
  `status: accepted`, `closed` today, `delivers` the confirmed features, no tasks and no
  branch, one line saying the work was done before Plexus and its history is in git.
  A feature is done when an accepted iteration delivers it; this keeps that rule true for
  work older than Plexus instead of adding an exception.
- `plexus/config.md` — the stack and the found commands, marked as found, not checked.
- `plexus/decisions/`, `plexus/backlog.md` — what the reading found for them; a file the
  reading has nothing for is not created.

## 6. The report

Keep three categories apart — it is what makes the report worth reading:

```
[stage1]init complete.

Confirmed:     3 features already working (iteration-00), 11 terms
Found, unchecked: the build and test commands — [stage4]setup runs them
Reconstructed: 2 decisions from the README, dates approximate
Existing code unchanged: git status is clean.
```
