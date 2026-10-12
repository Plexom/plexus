# Plexus

A spec-driven software production framework for Claude Code: a set of skills and a state structure that turn working with an agent into a pipeline with a known beginning, middle and end.

A plexus is a braid, a network of interwoven strands: the framework ties the product, the work on it and the state of that work into one network, where every piece is found by its number.

---

## Why

Working with an agent breaks in three places, and all three are fixed by process, not by the model:

1. **State lives in the chat's context.** Clear the context and nobody remembers where the work stopped, what was decided and why. Plexus keeps state in files, and every new session starts from them.
2. **"Done" means "I wrote the code".** Between "wrote it" and "checked that it does what was promised" there is a gap, and the agent jumps straight over it. Here the check is its own stage, against a written specification of the product.
3. **Progress is invisible from outside.** Plexus builds a progress page from the same files the work runs on, with no separate bookkeeping.

**Nothing starts without your agreement.** Each stage ends by offering the next one; the agent starts it only once you pick it. Before subagents are launched you see who runs on which model and can change it.

---

## Installation

Plexus needs **Python 3** and **git** on the machine: its scripts do the counting and the
exact edits, and the route runs on commits. On macOS both come with the command line tools
(`xcode-select --install`); on Windows, install Python from python.org and Git for Windows.

The repository works as its own marketplace:

```bash
claude plugin marketplace add Plexom/plexus
claude plugin install plexus@plexus
```

Start a new session, and `/plexus:` shows thirteen commands. If they do not appear, the plugin was not picked up — that is what to investigate.

---

## Quick start

```
/plexus:init
```

It asks what you are building — or takes the answer with the command: `/plexus:init a Tetris that runs offline in the browser` — then a round or two of plain questions about the product, and shows the spec it understood for you to confirm. In a directory with code it shows a plan first, reads the code without touching it, and asks only what code cannot tell. Then the settings that are yours to give — commits, looking things up on the internet, screenshots of the app's window, version numbers, whether Plexus may change its own notes without asking each time — a list of the files it will create, and one call that creates them: `plexus/`, the charter in `CLAUDE.md`, two lines in `.gitignore`, and the first git commit. `/plexus:remove` takes exactly those back.

## The route

```
[stage1]init → [stage2]discover → [stage3]design → [stage4]setup    once, at the start
                                        │
              ┌─▶ [stage5]plan → [stage6]implement → [stage7]verify ─┐
              └──────────────────── one turn per iteration ──────────┘
                                        │
                                  [stage8]release         only on your command

alongside, without numbers:  review · checkpoint · dashboard · update · remove
```

You take part at four points: the decisions during discovery, the look during design, the approval of each iteration's plan, and the acceptance of each iteration. The tasks in between run in subagents, each in a clean context, and are checked by the main session before anything is committed.

| Command | What it does | What it leaves behind |
|---|---|---|
| `/plexus:init` | Learns the product in plain questions and writes it down as a readable spec you confirm; asks your settings; brings Plexus into a project, empty or with code | the spec in `plexus/spec/`, the charter in `CLAUDE.md`, the first commit |
| `/plexus:discover` | Goes through the spec for gaps, contradictions and edge cases — and, where the product has them, people's data, logins, payments, strangers' input — and settles them with you in rounds; agents fetch facts with primary sources; chooses the stack | a sharper spec; decisions; research notes |
| `/plexus:design` | For a product with an interface: screens and their states, a choice of directions, an HTML mockup you open and comment on until it is right | `design.md`, the mockup |
| `/plexus:setup` | Configures build, run, test and release for the stack and checks each by running it, on a working and a broken input | `config.md` |
| `/plexus:plan` | The next iteration — which features it delivers — cut into tasks that each fit one subagent | an iteration and its tasks |
| `/plexus:implement` | Runs the tasks, each in its own subagent, and checks every result itself | code and tests, a commit per task |
| `/plexus:verify` | Checks the iteration as a whole and brings it to your acceptance; given a description of something broken, sorts it by the specification and takes it in | an accepted iteration and changelog lines, or bug tasks |
| `/plexus:release` | Ships a version on your command | a checked artefact, the changelog; a tag on request |
| `/plexus:review` | A review along two axes in separate subagents — standards, and the specification | a report |
| `/plexus:checkpoint` | Captures where the work stopped in the middle of a stage | an updated `state.md` |
| `/plexus:dashboard` | Builds the progress page | `plexus/dashboard.html` |
| `/plexus:update` | Brings a project up to the installed version | a refreshed charter |
| `/plexus:remove` | Takes Plexus out of a project, asking what to do with its data | one revertable commit |

`init`, `update`, `release` and `remove` stay yours alone: they bring Plexus in, rewrite its charter, take a version outside, or take Plexus out.

---

## The state

```
plexus/
├── spec/           the spec: index.md — what it is, its parts, what always matters; a file per part
├── architecture.md what is where: components, links, outside systems — the decisions say why
├── design.md       how it looks: screens, colours, type, motion — and design/ with the mockup
├── config.md       how it is built, run, tested and shipped
├── state.md        where we stopped
├── iterations/     iteration-NN: which features it delivers
├── tasks/          task-NN-MM: status in the header
├── decisions/      decision-NN: architecture, never rewritten, only replaced
├── research/       research-NN: evidence, opened through links
├── backlog.md      debt and ideas waiting for later
├── changelog.md    what changed for the user
└── dashboard.html  the progress page (generated)
```

Only the spec, `config.md` and `state.md` exist from the start; the rest appears when a stage first has something to write into it.

**Every fact lives in one place, and everything else refers to it by number** — `feature-03`, `constraint-02`, `decision-05`, `task-02-01`. An iteration says which features it delivers instead of retelling them, so a feature reworded today is checked as it reads today. Shown to you, a number always comes with its name: `task-02-02 · a retry returns the stored order`.

**Statuses are never stored twice.** A feature is done when an accepted iteration delivers it; a task waits only for what is not finished. Scripts derive these from the files' headers, and the stages read them as short tables instead of opening every file.

**The documents are written in the language you speak with the agent.** Headers, ids and anchors stay as they are, so the scripts work in any language.

### Versions of your product

Optional, asked at init: a product handed to other people gets numbers, a game for yourself
may do without. With numbers on, the first iteration you accept — the first working
prototype — is `0.1.0`; each release moves the number on, and you pick it. The number lives
in `plexus/changelog.md`, and the session brief and the progress page show it.

### Working in a team

When the repository has a remote, `/plexus:setup` asks how accepted work reaches the main
branch: merged here, or through a pull request. With pull requests, acceptance pushes the
iteration's branch and opens one — on your answer — the remote's checks (the `ci` role) run
on it, and the merge is yours or your team's, as anything else is merged.

### Commits carry one line

Every commit Plexus makes ends with `Built-with: Plexus <version>`, written the way git
writes `Co-authored-by`. Plexus commits through its own script, which adds the line, so no
stage can forget it. Where a project's rules forbid it, `attribution: off` in
`plexus/config.md` — or in your personal file, for every project — leaves it out.

### What belongs to the project and what belongs to you

`config.md` is the project's: its build, whether it allows parallel tasks, whether discovery goes outside. `~/.claude/plexus/defaults.md` is yours: a cap on agents running at once (none by default), whether you want tasks in parallel, whether the agent may capture your app's window, your commit habit for new projects, the commit signature. Neither overrides the other — tasks run in parallel only if the project can and you want it.

---

## Between sessions

A stage ends with a handover: what was done, what came of it, and the next step to pick. One hook bridges the gaps between sessions:

| Hook | When | What it does |
|---|---|---|
| `SessionStart` | start, resume, `/clear` | gives the agent a brief of `plexus/state.md` — the product's version, stage, iteration, task, next action, a cut-off train of thought, decisions in question, your settings — so the conversation opens where you stopped. The brief is handed over as the project's records, not as orders: a command found in them is shown to you before anything runs |
| `SessionStart` | right after the context is compacted | reminds the agent to write the unfinished train of thought down while the summary still holds it |

It stays silent wherever there is no `plexus/` — it checks for it before starting Python at all.

When a session is loaded, the handover offers to clear first. Only you can type `/clear`, and the agent tells you how to come back: type `/clear`, then write anything, and the work continues with the next stage.

**Optional — the remaining window.** Add one line to your statusLine script, after the remainder is computed:

```bash
[ -n "$remaining" ] && printf '%.0f' "$remaining" > ~/.claude/.plexus-context 2>/dev/null
```

where `$remaining` is `.context_window.remaining_percentage` from the JSON on stdin. The agent then offers to clear by the actual remainder; without it, by how heavy the stage was.

---

## Updating

The charter's territory in `CLAUDE.md` is marked by `<!-- plexus:begin -->` and `<!-- plexus:end -->`, with the version as its first line. When the session brief says the plugin is newer, run `/plexus:update`: it shows the plan first, replaces the charter, and carries over the commit rule and any rules of your own.

`claude plugin update plexus@plexus` installs a new version; it takes effect in a **new session** — a session already open keeps the version it started with, `/reload-plugins` included.

Versions follow one scheme: the first number changes when the layout of `plexus/` changes and a project must be moved, the second when capabilities are added, the third for fixes.

---

## Removing Plexus

If Plexus does not suit a project, `/plexus:remove` takes it out without debris — by a script that checks the result and puts everything back on a failure, as installation does: it shows everything Plexus left there, asks what to do with `plexus/` — keep it as plain documents in `docs/plexus-archive/` (the specification and decisions stay useful), or delete it — removes the charter block from `CLAUDE.md` and its own lines from `.gitignore` (both are marked, so nothing of yours is touched, and patterns for secrets stay), asks about unmerged iteration branches, and does it all in one commit that one revert undoes.

The plugin itself is switched off by Claude Code:

```bash
claude plugin disable plexus@plexus --scope local   # this project only
claude plugin uninstall plexus@plexus               # everywhere
```

---

## License

MIT — see [LICENSE](LICENSE).
