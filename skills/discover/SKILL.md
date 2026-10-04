---
name: discover
description: In a project with plexus/: goes through the spec in plexus/spec/ for gaps, contradictions, edge cases and undefined words, settles them with the user in rounds of plain questions, and makes the technical choices, the stack among them, with subagents fetching sourced facts. Use after init, for a new direction, or to revisit a decision.
argument-hint: [what to look into, or a decision to revisit, in one line]
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" *) Skill(plexus:design) Skill(plexus:setup) Skill(plexus:plan) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# [stage2]discover

A file this stage writes that does not exist yet is created from its template, in the
document's language — the templates, printed here so they need not be read:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" decision research backlog architecture 2>&1
```

Init gathered the product and wrote it down. This stage **reads that
spec critically**: what does it leave open, where does it contradict itself, what happens
at the edges nobody described, how will it be built. The most common cause of failure is
not bad code but a different understanding of the task — or a platform limit found after
the code was written. Both are cheapest to close now, on a page of text.

Two kinds of work run side by side and must not be mixed up: **facts are your job,
decisions are the user's.** Never ask the user for a fact you can look up, and never make
a decision on their behalf, not even an obvious one.

## 1. What this run is about

Read the spec: its front page, `plexus/spec/index.md`, then the parts this run is about —
on the first run every part, since this is the one stage that needs the whole picture; for
a product with many parts, a part at a time, each run settling one part before the next
(the front page's list shows which are done). Then
`plexus/config.md`: `research` says whether agents may look things up outside — `private`
means they may, but a query names the technology and the question only, never the product,
its name or its details: the brief each agent gets is written that way. "Now" in
`plexus/state.md` lists what init left open. Then the decisions in force:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" decisions 2>&1
```

Open a decision in full only when this run touches it. What is already decided is not
asked again, and what the user said at initialization is not asked twice.

- **The first run after init** — analyse the whole spec, below, in the order of section 3:
  what it means first, how it behaves next, how it is built last.
- **A named question** — the argument, or a handover such as "revisit `decision-05`" —
  only what depends on it is asked, and the run ends when that is settled. A settled
  decision it touches is asked about explicitly, never changed quietly.
- **No argument on a project with decisions** — do not open with an empty "what shall we
  look into?": the user may have been away for a day. Offer, in `AskUserQuestion`, what the
  records suggest — decisions in question, "revisit if" signs that have appeared, open
  questions in `state.md` and the iterations, what planning stopped on for lack of a
  decision, recent ideas in `plexus/backlog.md` — with "Other" for their own.

## 2. Read the spec for what it leaves open

Before asking anything, go through the spec yourself. Look for:

- **Words the user left open** — init marks them "to be clarified": "light", "graphic",
  "simple". Each can mean several things, and a choice made on a guessed meaning is made
  on nothing. They come first.
- **The edges of each thing it does** — empty, too much, missing, broken, interrupted,
  repeated, two at once. For a game with a word on a cleared row: two rows at once — one
  word or two? The word file missing or empty? A word too long for the field?
- **Contradictions** — two lines that cannot both hold, or one that makes another
  expensive: "light" and "a glow on every block" pull against each other on a weak laptop.
- **What is implied but never said** — the settings file: where it lives, who edits it,
  what happens to a typo in it.
- **Words used loosely** — "record" means the best score, or every game played?
- **What always matters, with no way to check it** — "smooth" is checked by what, on which
  screen?
- **What could hurt someone** — asked only where the product has it, never walked as a list
  for completeness: people's data it keeps — what, where, who sees it, how it is erased; a
  way in — accounts, roles, who may do what; money it takes; input from strangers over a
  network; people who will use it with a screen reader or the keyboard alone, when it is
  public. Asked about a situation, as everything else: "Someone forgot their password —
  what happens?", "Who can see another person's orders?". Each answer becomes a constraint
  with its check. A game kept on one's own laptop has none of this, and nothing is asked.
- **How it will be built** — the platform, the storage, the stack; every choice that is
  expensive to undo. A platform limit belongs here: "a page opened from disk cannot write
  a file by itself" changes what is possible.

Hold what you find as a tree: some questions only make sense once another is answered —
which word to show for two rows waits until it is settled that a word is shown per row at
all. **The questions that can be asked now** are those whose premises are settled; the rest
wait for their round. Keep this structure to yourself: the user sees questions, not a tree.

**How it is built waits for what it is.** The rounds go in this order: the words left
open; then the behaviour, part by part, until the spec describes the whole product and the
user has confirmed it; only then the technical choices. A stack picked while the rules of
the game are still open is picked for a product nobody has described yet — and every
behaviour settled afterwards is quietly bent to fit it.

Never ask why the product should exist or how its success will be measured: a person
building something for themselves has no business case to recite. What they say about it
unprompted is written down.

## 3. A round

Ask **every question that can be asked now in one round**, with `AskUserQuestion`, up to
four per call, consecutive calls for more, the ones nearer the root first.

**About a concrete situation**, by the rule on asking in `CLAUDE.md`: not "Define the
constraint for frame rate", but "The game will run on your 120 Hz screen. Is it enough that
it looks smooth to you, or should it hold 120 frames under load — a full field, the glow
on?" A short `header` names the subject; the recommendation's reasoning is in its
description; each real alternative says what it gives or costs. "Other" carries the answer
nobody foresaw — do not pad to four.

**A technical choice is explained by its consequences**, not its jargon: "Where do the
records live? In the browser — nothing to install, but they stay in this browser only. In
a file next to the game — you can copy it, but the game then needs a small local helper to
write it." The user decides what they get; the name of the technology is yours to add.

**The stack — and any choice that shapes what the product can be — is never offered from
memory.** When the technical round begins, read
`${CLAUDE_PLUGIN_ROOT}/skills/discover/references/stack.md` and follow it: what is current,
the new beside the proven, each option's maturity and what the user gets and cannot get.

A question you cannot offer a single option for is not ready: something it rests on — a
fact to look up, another answer — is still open. Settle that first. What remains open after
that is asked as plain text, one sentence.

Then **wait for the answers**, and **write them down before the next round** — see "What
each answer becomes" — and say in one line what changed in the spec: "Спека обновлена:
очистка линий — два новых случая; рекорды — слияние из файла". A round recorded is a round
that survives `/clear` or a broken session; nothing that matters may live only in the
conversation.

When the behaviour is settled, before the technical rounds, show the spec as it now reads —
its parts and what each does, in a few lines each — and ask whether it is the product the
user means. The technical choices are made for that text.

## 4. Facts: agents with sources

When a question needs a fact — what the platform allows, how the existing code is built,
what others do — find it out: in the project yourself, in the outside world by an agent if
research is on or private. If it is off and a question plainly needs the outside world, say so once,
in a line, with what deciding without it costs.

**One agent, one checkable question.** "Study browser storage" has no answer by which the
work could be called finished; "can a page opened from a file:// address write a file to
disk without the user picking it each time" does. **Only independent questions go at
once**: a question whose answer could make another pointless goes first, and the dependent
one waits. While agents work, ask the rest: only what sits below an open fact waits.

Before launching, say in one line how many agents, on which model, what each looks for.
Fetching facts and links is cheap-model work; you draw the conclusions from what returns.

**A conclusion without a link to a primary source is a guess.** A model states
nonexistent limits and APIs with full confidence, and the source is the only way to tell.
An agent that returns claims without links goes back to work. Demand the date and version
too: a limit lifted two years ago and one that still holds read the same.

Each looked-up question becomes `plexus/research/NN-<topic>.md`, `id: research-NN`: the
limits, what remains unknown — honestly, since an invention in a report is
indistinguishable from a fact a week later — and where the conclusions went. `confidence`
follows the sources: official documentation — `high`, discussions and others' experience —
`medium`, a single unconfirmed post — `low`. Then check the file rather than trusting the
write: it is non-empty, `date` is today's, "Sources" holds links, every conclusion has one.

A limit that was found does not become a decision by itself: it goes into the next round
as a premise, in plain words, and the user decides.

## 5. What each answer becomes

Sorting is your job, not the user's. Each answer has one home:

| The answer is about | It goes to |
|---|---|
| What the product does — a behaviour a person can check | the spec, in the part of the product it belongs to: the item with its `feature-NN` tag, its text now covering the edge case; a new item, ending with `` `feature-NN · MVP` `` or its scope, when it is new; a new part when none fits |
| What must hold whatever else changes — speed, limits, dependencies, permissions, people's data, access, payments | the spec's front page, a `constraint-NN` row with how it is checked |
| What the product deliberately does not do | the front page, "What we deliberately do not build" |
| A word the product uses | the front page, "Terms", with the identifier the code will use |
| How it is built, and it is expensive to undo or the code will not explain why | `plexus/decisions/NN-<slug>.md`, `id: decision-NN`, with "Rests on" (linking a `research-NN` where one exists) and "Revisit if" |
| The stack | A decision as above, and the `stack` field of `plexus/config.md` |
| How the system is divided — its components, who calls whom, the systems outside it | `plexus/architecture.md`: a `component-NN` row each, with the spec parts it serves and where it will live in code; the links; the outside systems; the diagram. Created when the stack is chosen, from the decisions just made — a decision says why, the map says what is where |
| How it looks — screens, style, motion | noted for the design stage in `state.md`; the design itself is not settled here |
| An idea that does not fit now | `plexus/backlog.md`, "Ideas" |

A decision is written per decision, not per conversation: three decisions, three files.
The spec is edited in place, and stays readable top to bottom — git keeps its history; a
decision is never rewritten.

## 6. A decision or a feature in question

When this run revisits something in question: the options, facts and research as for any
decision, then the user's choice. A replaced decision gets `status: superseded` and
`superseded_by`; the new one takes its place. Find everything that refers to the old id —
tasks, iterations, other decisions — and show it: what depended on the old answer has to be
looked at again, not assumed still right.

## 7. When it is over

When nothing is left that can be asked — or the named question is settled: every branch
walked, nothing left implied. Not sooner, and not later: questioning for completeness after
the questions ran out is questioning for its own sake. Show what changed in the spec and
what was decided, in plain words with ids beside them, and ask with `AskUserQuestion`
whether it matches what they meant, or something is off.

## Signs that you are cutting corners

- One question asked when more could be asked now, or questions printed as a list.
- The user asked something you could have looked up, or a decision made for them.
- A round not written down before the next one started.
- An edge found and filled with your own guess instead of asked.
- A research note claims something none of its sources says.
- The stack offered from what is familiar only — nothing newer looked for, or a new option
  shown without its maturity and its costs.

## Handover

```
[stage2]discover complete: nothing left open.

Settled:   9 questions over 3 rounds; the edges of 4 things it does
Decided:   stack — a single HTML page with a small local helper for files (decision-01)
Recorded:  2 new things it does, 1 more that always matters; 3 decisions
Looked up: 2 questions, 11 sources, confidence high
Unknown:   how the glow performs on integrated graphics — no data found

Next: [stage3]design — screens, style and a mockup to look at before any code
```

The next stage is design when the product has an interface a person looks at; otherwise
setup, when this run chose the stack or changed how the project is built; plan, when it only
answered a question in a project whose build already works. Then one `AskUserQuestion`,
recommended first: the next stage; **another round**, if something is still unsettled; **stop**, saying where the
work picks up. The commit is offered by the commit rule.
