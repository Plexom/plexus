#!/usr/bin/env python3
"""The state as short tables, read from headers and numbered rows.

A stage needs to know which tasks are open and what each waits for, which
features are still to be done, which decisions are in force. Opening every file
for that fills the context with work already finished; the answers are in a few
lines of each file. So the stages read these tables and open only what they are
about to work on.

Run from the project root:
    python3 tables.py              all three, unfinished only
    python3 tables.py tasks        open tasks and what each still waits for
    python3 tables.py features     features not done yet, and the MVP count
    python3 tables.py decisions    decisions in force and in question
    python3 tables.py state        plexus/state.md as it is
    python3 tables.py git          uncommitted changes and the last commits
    add --all to include what is finished, dropped or replaced

`state` and `git` are here so a stage substitutes where the work stopped with the
one command it is already allowed to run: a `cat` or `git status` of its own is a
command outside the stage's permissions, and outside auto mode that stops the call.

A stage runs this in its `!` block, where any exit code but 0 cancels the whole stage
before Claude reads a word of it — and the stage that would fix an unreadable file
is exactly the one that then never loads. So what went wrong is said in the output:
no plexus/ here, or the files left out of the tables, each with why.
Exit code: 0 — always, but for a table name it does not know (1).
"""
import subprocess
import sys

from plexus_state import (ROOT, STATE, SKIPPED, CLOSED_TASK, OPEN_ITERATION, load, ids,
                          feature_status, task_waits)


def clip(text, n=60):
    text = str(text)
    return text if len(text) <= n else text[:n - 3] + "..."


def table(rows):
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]) - 1)]
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)) + "  " + r[-1])


def tasks_table(s, show_all):
    tasks = s["tasks"]
    closed = [t for t in tasks if t.get("status") in CLOSED_TASK]
    done = sum(1 for t in closed if t.get("status") == "done")
    print("Tasks: %d open of %d (%d done, %d wontfix)"
          % (len(tasks) - len(closed), len(tasks), done, len(closed) - done))
    shown = tasks if show_all else [t for t in tasks if t.get("status") not in CLOSED_TASK]
    if shown:
        rows = [("id", "status", "size", "type", "feature", "waits for", "title")]
        for t in sorted(shown, key=lambda x: x["id"]):
            kind = t.get("type") or "feature"
            sev = t.get("severity")
            if kind == "bug" and sev and sev != "none":
                kind = "bug:%s" % sev
            waits = task_waits(t, s["tasks_by_id"], s["decisions_by_id"])
            rows.append((t["id"], str(t.get("status", "")), str(t.get("size", "")), kind,
                         ", ".join(ids(t.get("feature"))) or "—",
                         ", ".join(waits) or "—", clip(t.get("title", ""))))
        table(rows)
    elif tasks:
        print("No unfinished tasks.")
    else:
        print("No tasks yet.")
    open_its = [i for i in s["iterations"] if i.get("status") in OPEN_ITERATION]
    if open_its:
        print("Iterations open: " + ", ".join(
            "%s %s" % (i["id"], i.get("status")) for i in sorted(open_its, key=lambda x: x["id"])))


def features_table(s, show_all):
    feats = s["features"]
    status = {f["id"]: feature_status(f, s["iterations"]) for f in feats}
    counts = {}
    for st, _ in status.values():
        counts[st] = counts.get(st, 0) + 1
    mvp = [f for f in feats if f["scope"] == "mvp"]
    mvp_done = sum(1 for f in mvp if status[f["id"]][0] == "done")
    print("Features: %d done, %d in progress, %d open%s — MVP %d of %d done"
          % (counts.get("done", 0), counts.get("in progress", 0), counts.get("open", 0),
             (", %d dropped" % counts["dropped"]) if counts.get("dropped") else "",
             mvp_done, len(mvp)))
    shown = feats if show_all else [f for f in feats if status[f["id"]][0] in ("open", "in progress")]
    if shown:
        rows = [("id", "scope", "status", "part", "feature")]
        for f in shown:
            st, it = status[f["id"]]
            rows.append((f["id"], f["scope"] or "—", "%s · %s" % (st, it) if it else st,
                         f.get("part") or "—", clip(f["text"], 70)))
        table(rows)
    elif not feats:
        print("No features recorded in the spec yet.")
    print("Constraints: %d — checked on every iteration" % len(s["constraints"]))


def decisions_table(s, show_all):
    decs = s["decisions"]
    by = {}
    for d in decs:
        by.setdefault(d.get("status", ""), []).append(d)
    print("Decisions: %d in force, %d questioned, %d superseded"
          % (len(by.get("accepted", [])), len(by.get("questioned", [])), len(by.get("superseded", []))))
    shown = decs if show_all else [d for d in decs if d.get("status") != "superseded"]
    if shown:
        rows = [("id", "status", "decision")]
        for d in sorted(shown, key=lambda x: x["id"]):
            st = str(d.get("status", ""))
            if st == "superseded" and d.get("superseded_by"):
                st += " → " + ", ".join(ids(d.get("superseded_by")))
            rows.append((d["id"], st, clip(d.get("title", ""), 70)))
        table(rows)
    elif not decs:
        print("No decisions recorded yet.")


def state_file(s, show_all):
    path = STATE / "state.md"
    if not path.is_file():
        print("No plexus/state.md.")
        return
    print(path.read_text(encoding="utf-8").rstrip("\n"))


def git_state(s, show_all):
    def git(*args):
        try:
            p = subprocess.run(["git"] + list(args), stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, universal_newlines=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return None
        return p.stdout.rstrip("\n") if p.returncode == 0 else None
    status = git("status", "--short")
    if status is None:
        print("Git: not a repository")
        return
    print("Uncommitted:" + (" none — the working tree is clean" if not status else ""))
    if status:
        print(status)
    log = git("log", "--oneline", "-15")
    print("Last commits:" + ("\n" + log if log else " none yet"))


def main(argv):
    if not STATE.is_dir():
        print("No plexus/ in %s or any folder above it — not a project with Plexus; there is "
              "nothing to read here. /plexus:init brings Plexus into a project." % ROOT)
        return 0
    show_all = "--all" in argv
    which = [a for a in argv if not a.startswith("--")]
    s = load()
    parts = {"tasks": tasks_table, "features": features_table, "decisions": decisions_table,
             "state": state_file, "git": git_state}
    chosen = which or ["tasks", "features", "decisions"]
    unknown = [w for w in chosen if w not in parts]
    if unknown:
        print("unknown table: %s — use tasks, features, decisions, state or git" % ", ".join(unknown), file=sys.stderr)
        return 1
    for i, name in enumerate(chosen):
        if i:
            print()
        parts[name](s, show_all)
    if SKIPPED:
        print("\nUnreadable, left out of the tables above, so they are incomplete: %d — "
              "tell the user and fix these before relying on the counts:" % len(SKIPPED))
        for path, why in SKIPPED:
            print("  %s — %s" % (path.relative_to(ROOT) if path.is_absolute() else path, why))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
