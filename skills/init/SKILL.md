---
name: init
description: Brings Plexus into a project - learns the product from the user in a few rounds of plain questions and writes it down as a readable spec they confirm, asks the settings that are theirs to give, then deploys plexus/, the charter in CLAUDE.md and the .gitignore lines in one call and makes the first git commit. An empty project starts from what the user says, one with code from a read-only scan. Use when the user starts a new project with the framework, or wants to attach it to a working repository.
argument-hint: [what we are building, in a sentence or two]
disable-model-invocation: true
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ground.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/deploy.py" *) Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" *) Skill(plexus:discover)
---

# [stage1]init

Brings Plexus into a project, once. It **gathers**: what the product is, in the user's
words, until it can be written down as a spec the user recognises as theirs. Finding the
holes in that spec is the next stage's work, `[stage2]discover`, done on the written text.
Then the settings, one list of files, one deployment, the first commit.

## 1. Look at the ground without narrating it

Already looked at, before your first move — do not check again with commands of your own:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ground.py" 2>&1
```

**Speak only if the check finds something that changes the course:**

- **Plexus is already here** — `plexus/`, the block, or broken markers. Stop and say so in one line:
  `/plexus:update` brings an older deployment up to date. Initialization never runs
  over one — the state in it is the project's work. Only one of the two present is a
  damaged deployment: name which, and stop.
- **Code is here** — files besides documents, or a history longer than a couple of commits.
  Follow the reference printed below: a plan, the user's confirmation, a read-only scan —
  then step 2 asks only what the code cannot tell.

An empty directory and an uninitialized git are what this command is for, not news:
a check that found nothing has nothing to report, now or on any later screen. A
README, a licence or a list of ideas do not make a directory non-empty.

The templates the deployment is written from, in the format it reads back:

```!
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/deploy.py" --templates 2>&1
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/templates.py" existing-code 2>&1
```

## 2. The product, in the user's words

Given with the command: $ARGUMENTS

If a description came with the command, it is the opening answer. Otherwise ask, as plain
text: **what are we building?** — two words or two paragraphs.

Then **rounds of questions about the product**, until it can be written down as a spec.
What a spec needs, and what to ask about when the description does not say it:

- who uses it, and where — at a desk, on a phone, offline;
- the main way through it, from the first screen or command to the end;
- the moments that make this product what it is — for a game, a line cleared, the game
  lost, a record set; for a tool, the input it takes and what it gives back;
- what matters most in how it feels — fast, light, smooth, private, simple;
- what it deliberately does not do;
- how it should look and feel, when it has an interface — the mood, what it resembles.

**Ask the way a person talks about their product**, by the rule on asking in the charter
printed above: "What should happen when a row is cleared?", never "What should always be
true?" — sorting the answer into the spec is yours.

**Do not ask what was already said.** "Light, smooth at 60/120 Hz" in the description is
an answer; a question that makes the user repeat it is noise. Ask what it leaves open.

**Do not interpret what was said either.** "Light" may mean small files, few features or a
cool laptop; "graphic" may mean anything from a clean look to a shader show. A word like
that is not given a meaning: it goes into the spec marked "to clarify", with the readings
it allows, and discovery asks about it first — before anything is chosen on the strength of it. Do not ask "why
this product" or "how will you know it worked": a person building a game for themselves
has no business case to state; a goal they bring up themselves is written down.

Options come from the description and from what is usual for this kind of product. Up to
four questions a round; a follow-up round only for what the answers opened.

**Not here:** how it is built — the platform, storage, a framework — and anything that
needs facts from outside. Those are decided in discovery, with sources. When the user
brings one up, note it for discovery and move on. Stop when the next question would be
about a detail that only matters once the whole is written down: usually after one to three
rounds. The answers live only in this conversation until step 5 — a long gathering is lost
with a broken session.

## 3. The spec — shown, then confirmed

Write out, in the conversation's language and the user's terms, how you understood the
product — short enough to read in one go:

```
Как я понял продукт

Что это        Тетрис в браузере, открывается локально, без интернета.
Что умеет      • классический тетрис: фигуры, повороты, падение
                 (первая версия)
               • при очищенной линии появляется слово из файла
                 настроек игры (первая версия)
               • рекорды записываются в файл (первая версия)
Что важно      • «лёгкая» — что именно, уточним первым делом
всегда         • плавная анимация на 60 и 120 Гц; проверим записью
                 кадров
Чего не делаем • сетевой игры
Внешний вид    неон на тёмном фоне, свечение фигур
Открыто        как странице писать файл рекордов — решим дальше
```

Then one `AskUserQuestion`: **it is right** (recommended), or a correction through
"Other". A correction changes the spec, and only what changed is shown again.

## 4. Settings

`AskUserQuestion` takes four questions at most: the first four in one call, the rest in a
second; skip a question the ground check already answers. Each in plain words, the reason in
the option's description, recommended first:

- **Commits**: without asking (recommended, unless the Defaults line names another habit —
  a stage that finished well has nothing to confirm, and one revert undoes a commit), or
  ask after each stage. Whatever the answer, each task's work is committed before the check
  at the end, which reads commits.
- **Looking things up on the internet** in the next stages — a search engine sees every
  query, so the options say what leaves the machine: yes, with the reason this product
  needs it — a platform's rules, someone else's service; **yes, without the product** —
  queries name the technology and the question, never the product or its details, for an
  idea or a company's system that is not public; or no.
- **Screenshots of the app's window**, for a product with an interface, unless the Defaults
  line already says `allowed` or `not allowed`: allow — the agent checks what is on screen
  itself; only that window, never the whole screen; the picture goes to Claude like any
  message, lies in a temporary folder outside the project and is deleted when the stage
  ends — or not — the user is asked what they see.

- **Version numbers** for the product: yes — the first working prototype, the first
  iteration the user accepts, is numbered `0.1.0`, and each release moves the number on;
  or not needed — a game or a tool for oneself does without, and saying so later switches
  them on. Recommended by the description: something handed to other people, installed
  or published — yes; something for the user alone — not needed.

- **Changes to Plexus's own files**: every step rewrites its notes — the spec, the plan,
  where we stopped — and each change asks for approval. In plain words, never a rule's
  syntax or a settings file's name: without asking (recommended) — only Plexus's notes in
  this project, never your code or other files, and only for you; or ask each time.

**A rule in an existing `CLAUDE.md`** that contradicts the charter printed above goes into
the second call: which takes precedence.

## 5. Say what will be created, then deploy

In the conversation's language, the real path, one line per file — then deploy at once,
without asking again:

```
Создам в /Users/alex/Projects/tetris:
  plexus/spec/        спека — то, что мы только что согласовали: титульная
                      страница и по файлу на каждую часть продукта
  plexus/config.md    настройки проекта
  plexus/state.md     где мы на маршруте
  CLAUDE.md           правила работы Plexus для Claude — новый файл
  .gitignore          пара строк Plexus и шаблоны, не пускающие секреты в git
  git                 новый репозиторий и первый коммит с этими файлами
  ~/.claude/plexus/defaults.md
                      ваш ответ про скриншоты — для всех ваших проектов, вне git
  .claude/settings.local.json
                      правило «правки в plexus/ без подтверждения» — только
                      для вас и этого проекта, вне git
Ваш код и другие файлы не трогаю. Коммиты Plexus кончаются строкой «Built-with:
Plexus» — если она не нужна, скажите, и я её выключу. /plexus:remove уберёт Plexus обратно —
только это, ваши правила в CLAUDE.md останутся.
```

An existing file reads "your rules stay, the block goes at the end" or "a few lines
appended"; an existing repository reads "a commit with only these files". The personal
file is listed only when step 4 asked about screenshots — it is the one file outside the
project. The settings line only when step 4 chose "without asking". The line about the commit signature is left out when the Defaults line already
says `attribution: off`; asked to drop it, add `attribution: off` to `config.md`.

**The deployment is one call.** Fill the templates above — every section under its
`=== name` line — and send them in one heredoc:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/deploy.py" . <<'PLEXUS'
=== spec/index.md
…
=== spec/<part>.md
…
=== config.md
…
=== state.md
…
=== commit rule
…
PLEXUS
```

Add `--screenshots=allowed` or `--screenshots=not-allowed` when step 4 asked it. The ground
check named a repository root above the project: ask whether the first commit goes there
before deploying, and add `--in-parent-repo` only on a yes.

- the spec, **readable from top to bottom**, as a front page and a file per part:
  - `spec/index.md` — "What we are building": what it is and for whom, in two or three
    plain sentences, the look and feel in one line — the design stage starts from it; the parts, each
    with its file; what always matters as `constraint-NN` rows, a word still to be
    clarified marked so, how it is checked left for discovery; what it does not do.
  - `spec/<part>.md` — one per part of the product, named in its own words and drawn from
    what the user described — for a game: the play, the word on a cleared row, records,
    settings; in a project with code, from its modules, screens and routes. Each thing it
    does is a list item ending with its tag, `` `feature-NN · MVP` `` for the first version,
    `` `feature-NN · later` `` for the rest, ids running across all parts. A small product
    has one or two parts; a company system, as many as it has areas — never a part for
    one feature.
- `config.md` — `research: on`, `private` or `off` with its one-line reason; `versions: on`
  or `off` from step 4; `stack` only if the user
  named it; `parallel: not checked`.
- `state.md` — `stage: init`, `next: discover`, `updated` today; under "Now", what is left
  open for discovery, a line each — it starts from them.
- `commit rule` — the rule from step 4, in English like the charter it goes into, the
  user's words quoted beneath when it was reworded. The script puts it into the charter
  with the version, and writes `CLAUDE.md`, `.gitignore` and the commit itself.

Headings and prose in the conversation's language; header keys and values, ids, file
names and `<!-- plexus:... -->` anchors exactly as in the templates. A table row that
still holds a `<...>` example may stay — the scripts skip it until a stage fills the
table. **A prose section nothing fills yet** gets one plain line, not a placeholder and
not a stage name the user has never heard: "to be filled in at the next step", or "…in
the steps after it" for what comes later — in the conversation's language, as in
«Заполнится на следующем шаге». The script refuses a `<...>` left in prose or in a header.

Exit code `1` — nothing was written; the reason is printed; fix it and send again. Exit
code `2` — the files are in place but git could not commit: say what git said and how to
fix it, and after the fix commit `plexus/`, `CLAUDE.md` and `.gitignore` — do not run the
deployment again. The usual cause is a git that has never been told who commits: do not
send the user to a terminal — ask, as plain text, the name and email their commits should
carry, and set them for this repository only (`git config user.name`, `git config
user.email`, no `--global`): other projects of theirs stay as they were.

With "without asking" for Plexus's own files in step 4, after a deployment that exited `0`: add
`"Edit(./plexus/**)"` to `permissions.allow` in `.claude/settings.local.json` with the Edit
tool — or Write, creating `{"permissions": {"allow": ["Edit(./plexus/**)"]}}` when the file is
absent — keeping everything else in it. Claude Code shows that edit for approval: it is the
one approval that saves the rest. Never through a script, never in `.claude/settings.json`,
which is shared with everyone on the repository. The deployment has already put the file
into `.gitignore`.

## 6. Report and handover

```
[stage1]init complete.

Spec:      5 things it does (3 in the first version), 2 that always matter
Created:   plexus/, the charter in CLAUDE.md, .gitignore; commit 3f2a91c
Open:      how the page writes the records file — discovery settles it

Next: [stage2]discover — going through the spec for gaps and deciding how to build it
```

Then one `AskUserQuestion`, recommended first: **Discover** — questions about what the spec
leaves open, and the technical choices, with agents fetching the facts; or **Stop here** —
saying that next time the work picks up right here, with `[stage2]discover`. Once the user
picks discover, start it yourself.

## What not to do

- Do not write code, a skeleton or a build configuration: this stage installs the
  process, not the project.
- Do not write `plexus/`, `CLAUDE.md` or `.gitignore` by hand, before or after the
  script: its checks and its rollback cover only what it wrote.
- Do not put into the spec what the user did not say or plainly imply. Filling a gap
  with a guess hides it from discovery, which exists to find it.
