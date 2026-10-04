---
name: design
description: In a project with plexus/: the look of a product with an interface - screens and their states from the spec, visual directions to choose from, an HTML mockup iterated until the user accepts it, recorded in plexus/design.md. Use after discovery for a product a person looks at, or when its look changes.
argument-hint: [a screen or what to change in the look, in one line]
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" *) Skill(plexus:setup) Skill(plexus:plan) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commit.py" *)
---

# [stage3]design

A file this stage writes that does not exist yet is created from its template, in the
document's language — the templates, printed here so they need not be read:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" design 2>&1
```

Settles how the product looks and moves **before any code**, while changing it costs an edit
to one HTML file rather than to a dozen components. The user sees a picture and reacts to
it — "the glow is too much", "the word should fly in, not fade" — which no written
description draws out. What comes of it is written down exactly, so the tasks build that
and verification checks against it.

A product nobody looks at — a command-line tool, a service, a library — has nothing to
design: say so in a line, and offer the next stage.

## 1. What there is to work from

The spec — its front page, `plexus/spec/index.md`, with what always matters and the look in
the user's words, and the parts a person sees;
"Now" in `plexus/state.md` — what discovery noted for design; the decisions, for the
platform the screens must live on:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tables.py" decisions 2>&1
```

An existing `plexus/design.md` means this run changes a design, not starts one: read it,
and touch only what the argument or the user names. A behaviour the spec does not have
that design turns up — a pause screen nobody mentioned — is a question to the user and,
agreed, an item in its part of the spec: the design does not add what the product does on its own.

## 2. Screens and their states

From the features, the screens a person passes through, each with what is on it and what
they can do there — and **its states**: the first run, the usual one, empty, loading, an
error, the end. A state nobody drew is a state the code will improvise.

Show the list briefly, in the user's words, and confirm it with `AskUserQuestion`: as
shown (recommended), or a change through "Other". For a larger product, which screens the
first version needs takes `multiSelect`.

## 3. The direction — offered, not assumed

Two or three directions, one `AskUserQuestion` question, each option a direction: its
colours, type and motion in a line of description, and a `preview` sketching it — a
palette in words and hex, a sample of the type, how things move. The one closest to what
the user already said first, recommended. "Other" carries their own.

What always matters in the spec binds the direction: "light" rules out a heavy web font
and a glow that costs frames on a weak machine; say so in the option it affects rather
than dropping the option silently.

## 4. The mockup

One self-contained file, `plexus/design/mockup.html`: every screen from step 2, switchable
from the page itself, with the real content of the product rather than filler, the chosen
colours and type as named variables, and the motion running — the cleared row, the word
appearing. **No external requests**: it opens from disk, offline, and shows what the
product will look like, not what a CDN happened to serve. It is a picture, not the
product: no logic beyond what makes the motion and the states visible.

A design skill available in the session may build it; the choices stay the user's.

**Assets are bounded.** The mockup shows the look; it is not where the product's art is
produced. What it uses from outside — a photo, a model, a font, a library — is chosen by
the user from options you show, with its licence and size stated before anything is
downloaded; it goes into `plexus/design/assets/`, and its source, author and licence into
"Decided, and why". Nothing over a few megabytes is committed: a source file a tool works
from — a 100 MB model before it was reduced — stays outside `plexus/` and goes into
`.gitignore`, outside the Plexus markers. An effect that needs a production pipeline — a
3D character, a rig, animation — is shown in the mockup at the level that settles the
decision, and the rest becomes a feature in the spec, built by the tasks like any other.

Open it for the user — `open plexus/design/mockup.html` on macOS, `xdg-open` on Linux — or
give the path. Check it yourself too, by the rule on screenshots in `CLAUDE.md`.

## 5. Rounds of comments

Ask what to change, with `AskUserQuestion`: options from what a person usually reacts to
on this kind of screen — brighter or calmer, larger or denser, faster or softer motion —
and from what you see yourself — contrast too low, text that does not fit; "Other" for
their own. Each round changes the mockup, reopens it, and records in "Decided, and why"
what was tried and dropped. It ends when the user accepts the mockup — not when you like it.

## 6. Write it down

`plexus/design.md`, from the template:

- **Screens** — a `screen-NN` row each, with its states and the features it serves;
- **Visual language** — the exact values from the mockup: colour tokens, type, space and
  shape, motion with durations and curves. The code will use these names;
- **Accessibility** — text contrast against its background, keyboard use, what happens
  under the system's reduced-motion setting;
- **Decided, and why** — the choices, and what was dropped.

Then check the file rather than trusting the write: every screen from step 2 is a row; every
colour used in the mockup is a token; no `<...>` placeholder is left in prose.

## Signs that you are cutting corners

- A direction chosen for the user instead of offered.
- A mockup with lorem ipsum, or with only the happy state of each screen.
- A mockup that pulls fonts or scripts from the internet.
- Accepted on your own judgement, without the user having seen it.
- Values in `design.md` that differ from the mockup.

## Handover

```
[stage3]design complete: 4 screens, neon on near-black.

Screens:   game, pause, game over, records — 11 states drawn
Direction: neon on near-black, one monospace font, glow on the active piece only
Rounds:    3 — the glow toned down, the word now rises instead of fading
Recorded:  plexus/design.md; mockup in plexus/design/mockup.html

Next: [stage4]setup — how the project is built, run and tested
```

The next stage is setup when the build is not set up yet; plan when it is. Then one
`AskUserQuestion`, recommended first: the next stage; **another round** on the mockup; **stop**, saying where the work
picks up. The commit is offered by the commit rule.
