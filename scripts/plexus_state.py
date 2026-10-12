"""Reading the project's state: headers of iterations, tasks and decisions, the
numbered items of the spec and the rows of backlog.md, and the statuses derived from them.

Shared by the tables, the session brief and the progress page, so no two of them
can read the same file differently. Statuses are derived here and never stored:
a feature is done when an accepted iteration delivers it, a task waits only for
what is not finished yet. A stored copy of a status drifts from its source; a
derived one cannot.
"""
import re
from pathlib import Path


def find_root(start):
    """The project's root: the folder itself when it holds plexus/, else the nearest one above
    holding plexus/state.md — the way git finds .git.

    A session moves with a `cd`: after a role such as `cd web && npm test` it stays in web/,
    and a stage started there would report a project with Plexus as one without. Init,
    update and remove do not look up: a new project inside another must not find its parent's.
    """
    if (start / "plexus").is_dir():
        return start
    for folder in start.parents:
        if (folder / "plexus" / "state.md").is_file():
            return folder
    return start


ROOT = find_root(Path.cwd())
STATE = ROOT / "plexus"

# Files that could not be parsed: the page looks plausible without them, and a
# silent skip reads as "there simply isn't any". They are collected here and
# reported both in the output and in the exit code.
SKIPPED = []

ID = re.compile(r"^(iteration|task|feature|constraint|decision|research|backlog|screen|component)-(\d+)(?:-(\d+))?$")
OPEN_ITERATION = ("planned", "in-progress", "verify")
CLOSED_TASK = ("done", "wontfix")


def norm(value):
    """An id in its one written form: `task-2-1` and `Task-02-01` both become `task-02-01`.

    Ids are joined across files, and a hand edit that drops a leading zero would
    otherwise make a task belong to no iteration — a count that looks real and is not.
    """
    s = str(value or "").strip().strip("'\"").lower()
    m = ID.match(s)
    if not m:
        return s
    kind, a, b = m.groups()
    return "%s-%02d" % (kind, int(a)) + ("-%02d" % int(b) if b else "")


def ids(value):
    """A header list (`[task-02-01, task-02-02]`) or a single value as normalised ids."""
    if isinstance(value, list):
        return [norm(v) for v in value if str(v).strip()]
    return [norm(value)] if str(value or "").strip() else []


# A comment is `#` standing apart — after a space, followed by one or the line's end —
# as the templates write it: `status: todo   # todo | done`. A `#` inside a word or a
# number is the value's own: `C#`, `issue #12`.
COMMENT = re.compile(r"(?:^|\s)#(?:\s.*)?$")


def uncomment(value):
    return COMMENT.sub("", value).strip()


def frontmatter(path):
    """A file's YAML header as a dict. No external libraries: the fields are flat."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    data = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        value = uncomment(value)
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            value = [v.strip() for v in inner.split(",")] if inner else []
        data[key.strip()] = value
    return data, text[m.end():]


def _title(body, fallback):
    heading = next((l.lstrip("# ").strip() for l in body.splitlines() if l.startswith("# ")), fallback)
    # `task-02-01 · Key stored` — the id is already a field; the title is what follows it
    return re.sub(r"^[\w-]+\s*·\s*", "", heading)


def collect(folder_name):
    """Every state file in a folder that carries a header with an id.

    A file without one is not dropped silently: it goes into SKIPPED, because a
    task missing from a table reads as work that does not exist.
    """
    items = []
    folder = STATE / folder_name
    if not folder.is_dir():
        return items
    for path in sorted(folder.glob("*.md")):
        if path.name.startswith("_"):
            continue
        fm, body = frontmatter(path)
        if not fm:
            SKIPPED.append((path, "no YAML header"))
            continue
        if not fm.get("id"):
            SKIPPED.append((path, "no id field in the header"))
            continue
        fm["id"] = norm(fm["id"])
        if not fm.get("title"):
            fm["title"] = _title(body, path.stem)
        fm["path"] = path
        items.append(fm)
    return items


def table_rows(path, first_id=None):
    """Data rows of the markdown tables in a file, as lists of cells.

    A table's header is found structurally — the row directly above the |---|
    separator — never by its words, since headings and columns are written in the
    project's language. A row whose cells hold a template placeholder (`<...>`) is
    not data. With `first_id`, only rows whose first cell is an id of that kind.
    """
    if not path.is_file():
        return []
    rows, pending = [], None

    def placeholder(cells):
        # an inline code span may legitimately hold angle brackets; the rest may not
        return any(re.search(r"<[^>]+>", re.sub(r"`[^`]*`", "", c)) for c in cells)

    def commit():
        if pending is None or placeholder(pending):
            return
        if first_id and not norm(pending[0]).startswith(first_id + "-"):
            return
        rows.append(pending)

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            commit()
            pending = None
            continue
        if set(line) <= set("|-: "):
            pending = None
            continue
        commit()
        pending = [c.strip() for c in line.strip("|").split("|")]
    commit()
    return rows


# A spec item defines an id by ending with it: "… breaks into two lines. `feature-09 · MVP`".
# Only a tag at the very end defines; the same id in the middle of a sentence is a reference.
TAG = re.compile(r"`((?:feature|constraint)-\d+)(?:\s*·\s*([\w-]+))?`\s*$")
ITEM = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")


def tagged_items(path):
    """(id, scope, text) of every list item or paragraph of a readable spec that ends with a tag.

    The spec is written by topics of the product, in its own language, so nothing is
    found by headings or words: a block is a list item with its wrapped lines, or a
    paragraph, and it counts when it ends with an id in backticks.
    """
    if not path.is_file():
        return []
    blocks, cur = [], []

    def flush():
        if cur:
            blocks.append(" ".join(cur))
        cur.clear()

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", "<!--", "```")):
            flush()
            continue
        if ITEM.match(line):
            flush()
            cur.append(ITEM.sub("", line).strip())
        else:
            cur.append(stripped)
    flush()
    found = []
    for block in blocks:
        m = TAG.search(block)
        # a template example, as in the tables: the stage has not written this item yet
        if m and not re.search(r"<[^>]+>", re.sub(r"`[^`]*`", "", block[:m.start()])):
            text = " ".join(block[:m.start()].split()).rstrip(" —-:")
            found.append((norm(m.group(1)), (m.group(2) or "").strip().lower(), text))
    return found


def spec_files():
    """The files the spec is made of: plexus/spec/ — its front page first, then the parts.

    A file whose name begins with `_` is a template, not the spec.
    """
    files = []
    folder = STATE / "spec"
    if folder.is_dir():
        pages = sorted(p for p in folder.glob("*.md") if not p.name.startswith("_"))
        files += sorted(pages, key=lambda p: p.name != "index.md")
    return files


def product():
    """Features and constraints from the spec, found by their ids, in any language.

    Two shapes are read: rows of a table (`| feature-01 | … | MVP |`), and items of a
    readable spec that end with their tag. Ids run across the whole spec: an id defined
    twice — in one file or in two — keeps its first definition, and the second is
    reported, since two texts for one feature is a spec that says two things. Each
    feature carries the part it lives in, so a stage opens that part and no other.
    """
    features, constraints, seen = [], [], {}

    def add(path, ident, scope, text, check=""):
        if ident in seen:
            SKIPPED.append((path, "%s is defined here and in %s; only the one in %s is counted"
                            % (ident, seen[ident].name, seen[ident].name)))
            return
        seen[ident] = path
        part = path.stem if path.parent.name == "spec" else ""
        if ident.startswith("feature-"):
            features.append({"id": ident, "text": text, "scope": scope, "part": part})
        else:
            constraints.append({"id": ident, "text": text, "check": check, "part": part})

    for path in spec_files():
        for r in table_rows(path, "feature"):
            add(path, norm(r[0]), (r[2] if len(r) > 2 else "").strip().lower(), r[1] if len(r) > 1 else "")
        for r in table_rows(path, "constraint"):
            add(path, norm(r[0]), "", r[1] if len(r) > 1 else "", r[2] if len(r) > 2 else "")
        for ident, scope, text in tagged_items(path):
            add(path, ident, scope, text)
    features.sort(key=lambda f: f["id"])
    constraints.sort(key=lambda c: c["id"])
    return features, constraints


def backlog():
    """Backlog lines split into debt and ideas by the shape of their table.

    The block headings are written in the project's language, so the kind is taken
    from the table itself: debt carries four columns, an idea three.
    """
    debt, ideas = [], []
    for r in table_rows(STATE / "backlog.md", "backlog"):
        item = {"id": norm(r[0]), "text": r[1] if len(r) > 1 else "", "rest": r[2:]}
        (debt if len(r) >= 4 else ideas).append(item)
    return debt, ideas


PERSONAL = Path.home() / ".claude" / "plexus" / "defaults.md"


def attribution(root=None):
    """Whether Plexus signs what it makes: on unless `attribution: off` stands in the
    project's config or the person's file — off in either is off, since a company's rule
    about commits and a person's wish are both reasons enough."""
    state = Path(root) / "plexus" if root else STATE
    for path in (state / "config.md", PERSONAL):
        if path.is_file() and frontmatter(path)[0].get("attribution") == "off":
            return False
    return True


def signature(version, root=None):
    """The trailer every Plexus commit ends with — the one place it is decided."""
    return "\n\nBuilt-with: Plexus %s" % version if attribution(root) else ""


def versions():
    """(version, date) of each version section of the changelog, newest first: `## 1.2.0 — 2026-10-01`.

    The changelog is the one place a product's version lives: a number is given when
    the first working prototype is accepted and moved on at each release, and both
    write a section there. The current version is the first one found.
    """
    path = STATE / "changelog.md"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+v?(\d+\.\d+[\w.\-]*)\s*(?:[—-]\s*(\S+))?", line)
        if m and "YYYY" not in line:
            out.append((m.group(1), m.group(2) or ""))
    return out


def feature_status(feature, iterations):
    """(status, iteration id) of a feature, derived from the iterations that deliver it."""
    if feature["scope"] == "dropped":
        return "dropped", None
    delivering = [i for i in iterations if feature["id"] in ids(i.get("delivers"))]
    for it in delivering:
        if it.get("status") == "accepted":
            return "done", it["id"]
    for it in delivering:
        if it.get("status") in OPEN_ITERATION:
            return "in progress", it["id"]
    return "open", None


def last_accepted(iterations):
    accepted = sorted(i["id"] for i in iterations if i.get("status") == "accepted")
    return accepted[-1] if accepted else None


def task_waits(task, tasks_by_id, decisions_by_id):
    """What a task still waits for: unfinished blockers and questioned decisions.

    A finished blocker is no reason to wait, so the reader never has to open a
    done task to learn whether this one can start.
    """
    waits = []
    for b in ids(task.get("blocked_by")):
        blocker = tasks_by_id.get(b)
        if blocker is None:
            waits.append("%s (missing)" % b)
        elif blocker.get("status") == "wontfix":
            waits.append("%s (wontfix)" % b)
        elif blocker.get("status") != "done":
            waits.append(b)
    for d in ids(task.get("decisions")):
        decision = decisions_by_id.get(d)
        if decision is not None and decision.get("status") == "questioned":
            waits.append("%s (questioned)" % d)
    return waits


def load():
    """Everything a table or a page needs, read once."""
    iterations = collect("iterations")
    tasks = collect("tasks")
    decisions = collect("decisions")
    features, constraints = product()
    debt, ideas = backlog()
    return {
        "iterations": iterations, "tasks": tasks, "decisions": decisions,
        "features": features, "constraints": constraints, "debt": debt, "ideas": ideas,
        "tasks_by_id": {t["id"]: t for t in tasks},
        "decisions_by_id": {d["id"]: d for d in decisions},
    }
