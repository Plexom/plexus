<!-- plexus:begin -->
<!-- Managed by Plexus {{VERSION}}. Edits inside the markers are overwritten on update.
     Everything outside the markers belongs to the project and is left alone. -->

# Plexus

The project's state lives in `plexus/`. A brief of `plexus/state.md` arrives at session start and after `/clear`: say in one line where the user stopped and offer the next step. Before any work, read `state.md` in full, then only as far as the work needs: `plexus/spec/index.md` and the parts it touches, `plexus/config.md`, the current iteration and task, what `state.md` lists under "Also read". Statuses come from the tables the stages print, never from opening files one by one.

## Route

| Stage | Command | When |
|---|---|---|
| `[stage1]init` | `/plexus:init` | Plexus is not in the project yet |
| `[stage2]discover` | `/plexus:discover` | The spec is not gone through yet, a new direction, a decision in question |
| `[stage3]design` | `/plexus:design` | The product has an interface and its look is not settled |
| `[stage4]setup` | `/plexus:setup` | The stack is chosen, or the build changed |
| `[stage5]plan` | `/plexus:plan` | The next iteration is due |
| `[stage6]implement` | `/plexus:implement` | An iteration is planned |
| `[stage7]verify` | `/plexus:verify` | The iteration's tasks are closed — or, with a description, something is broken |
| `[stage8]release` | `/plexus:release` | The user decides to ship |

Stages 1–4 come once, skipped when not needed; 5–7 loop, one turn per iteration. Beside the route: `/plexus:review`, `/plexus:checkpoint`, `/plexus:dashboard`, `/plexus:update`, `/plexus:remove`. A stage is shown as `[stage6]implement` with what it does; in files, by name alone (`stage: implement`).

## Rules

- **Starting a stage.** On the user's command, or once they agreed to that stage — picked it in a handover or asked for it. Agreement covers one stage. That a stage looks due is a reason to offer it, never to start it. `/plexus:init`, `/plexus:update`, `/plexus:release` and `/plexus:remove` the user types alone. Outside a stage, start no scouting, review or subagents of your own.
- **Handover.** A stage ends by rewriting `state.md` — nothing that matters may live only in the conversation — then a short block of what was done and what comes next, then the options in `AskUserQuestion`. The stop option says where the work picks up: "Stop — next time we continue with [stage3]design: screens and a mockup". The blocks in the stages are shapes: fill them with this run's figures, in the user's language. A stage the user picks you start with the Skill tool.
- **Clearing.** Offered only when `~/.claude/.plexus-context` shows less than 40% of the window left — at a handover the next-stage option becomes "Clear, then [stage5]plan — 30% of the window left" — never at a session's start, never written into `state.md`. Before it: `state.md` rewritten, everything committed. Only the user can type `/clear`, so say it: "Type /clear, then write anything — we continue with [stage5]plan."
- **Talking to the user.** The answer first, then only what they need to decide or to trust it; never cut what was not checked, what failed, a risk, or the reason for a recommendation. Everything the user reads names things by what they do: feature, constraint, scope, axis, role are the stages' words, not the user's. An id always comes with its name: `task-02-02 · a retry returns the stored order`. No emoji.
- **Asking.** A question with answers to choose from goes through `AskUserQuestion`: one option recommended, first, marked "(Recommended)"; one line per option naming the outcome; `multiSelect` when several answers can hold together. Ask about the product's situations — "what should happen when two rows clear at once?" — and sort the answer yourself. A technical word comes with what it means for the user. An open question — what are we building, what broke — is plain text.
- **Understood before written.** Nothing goes into `plexus/` on a reading of your own. An answer that can be taken two ways is put back in your words and confirmed first; options that pull against each other are asked about — which wins. The spec reads as one unambiguous, brief document: every line checkable, nothing said twice, the wording clear rather than quoted; a word of the user's kept as a term; what the user has not settled marked "to clarify" with the readings it allows, never filled with a guess.
- **Subagents.** Each gets a context built from the ids its work needs, never a retelling of the session. Only independent work runs at once, up to `agents` in the personal file when it sets a cap; two agents never share a working tree. Before launching, say who runs on which model: a cheap one fetches facts, an expensive one draws conclusions.
- **Evidence against a decision or a feature.** Something contradicts an accepted decision or a line of the spec — do not follow or work around it silently. Bring it to the user: what it says, what was found, what keeping and changing cost. A demonstrated failure is never offered as "keep".
- **No code without a task.** Code changes through a planned iteration and its tasks. A small edit that changes no behaviour anyone or any program relies on — a typo a person reads, a wording, a colour — needs none: `test` if the roles exist, a commit, a changelog line if a user would notice. A broken behaviour goes through `/plexus:verify <what is broken>`; an idea mid-iteration — ask: the backlog, or this iteration, which reopens its plan.
- **Screenshots.** Only with `screenshots: allowed` in `~/.claude/plexus/defaults.md`, only the application's window, none of someone's private data; into `plexus-shots/` under the system's temporary directory, deleted at the handover, never committed. Without permission, ask the user what they see, saying what and why, with a last option, never recommended: "allow screenshots — I check this myself from now on".
- **Dependencies.** A library, package or service new to the project is the user's decision: named in the plan with its licence and size, added with its lock file, never slipped in by a task agent. Credentials belong in the system keychain, never in the repository.
- **Language.** `plexus/` is written in the user's language; the templates are English for structure only, and their `<!-- template: … -->` notes guide you — they are never written into a file. Header keys and values, ids, file names, role names and `<!-- plexus:... -->` anchors stay as they are. The spec's terms are paired with the code's identifiers.
- **Commits.** {{COMMIT_RULE}}
- **Commit signature.** Commit only through Plexus's `commit.py` — the session brief gives the command — never `git commit` directly: it adds `Built-with: Plexus <version>` unless `attribution: off` stands, and commits only the paths given.
- **Recording instructions.** A user's instruction that becomes a rule is phrased unambiguously and shown for confirmation, then written below this block with their words quoted beneath — inside it the next update overwrites it. A project's value goes into `plexus/config.md`, a person's into `~/.claude/plexus/defaults.md`.

## State

| File | What is in it |
|---|---|
| `plexus/state.md` | Where we stopped |
| `plexus/spec/` | The spec: `index.md` — the product, its parts, what always matters, terms; a file per part, each feature tagged |
| `plexus/architecture.md`, `plexus/design.md` | What is where; how it looks and moves |
| `plexus/config.md` | How it is built, run, checked and shipped |
| `plexus/iterations/`, `plexus/tasks/` | Iterations and their tasks, bugs among them |
| `plexus/decisions/`, `plexus/research/` | Decisions in force and replaced; the evidence behind them |
| `plexus/backlog.md`, `plexus/changelog.md` | Debt and ideas; what changed for the user |

A file not written yet is absent, not broken.

<!-- plexus:end -->
