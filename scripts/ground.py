#!/usr/bin/env python3
"""What is on the ground before init, update or remove acts: Plexus's marks, code, git.

Those stages begin by looking at the project, and left to compose that look
themselves, each run writes a different shell line. Such a line fails exactly
where the answer is "nothing here": `grep` on a missing CLAUDE.md, `ls` on a
missing directory — and an empty project, the most ordinary case for init, is
shown to the user as a failed command. A look written once answers the same way
every time, and one command is one permission rule instead of a handful.

**Absence is an answer, not an error**: every line says what was found or that
nothing was. The exit code is always 0 — a non-zero one would report the
ordinary case as a failure again. A part that could not be read says so in its
own line, and the rest is still printed.

Run from the project root:
    python3 ground.py [project directory]
Exit code: 0, always.
"""

import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PERSONAL = os.path.join(os.path.expanduser("~"), ".claude", "plexus", "defaults.md")
# a README, a licence or a list of ideas do not make a directory non-empty
DOC_EXT = {".md", ".markdown", ".txt", ".rst", ".adoc", ".org"}
DOC_NAMES = {"license", "licence", "copying", "notice", "authors", "contributors"}
SKIP_DIRS = {"node_modules", "plexus", "venv", "__pycache__", "build", "dist",
             "target", "vendor", "Pods", "DerivedData"}
FILE_CAP = 5000  # enough to tell a project with code from one without; a big tree is not walked to the end
EXAMPLES = 5
CHANGES = 20


def many(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def row(name, text):
    print("%-12s %s" % (name, text))


def git(root, *args):
    """Output of a git command, or None when it failed — no repository, no commits, no git."""
    try:
        p = subprocess.run(["git", "-C", root] + list(args), stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, universal_newlines=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def plexus_dir(root):
    path = os.path.join(root, "plexus")
    if not os.path.isdir(path):
        return "absent"
    names = sorted(os.listdir(path))
    return ", ".join(names) if names else "present, empty"


def charter(root):
    path = os.path.join(root, "CLAUDE.md")
    if not os.path.isfile(path):
        return "absent"
    lines = io.open(path, encoding="utf-8", errors="replace").read().splitlines()
    begin = [i + 1 for i, l in enumerate(lines) if "<!-- plexus:begin -->" in l]
    end = [i + 1 for i, l in enumerate(lines) if "<!-- plexus:end -->" in l]
    if not begin and not end:
        return "present, %d lines, no Plexus block" % len(lines)
    if len(begin) != 1 or len(end) != 1 or end[0] < begin[0]:
        # remove and update act on the block between the markers; broken markers
        # are for the user to see, not for a stage to guess around
        return "markers broken — plexus:begin on lines %s, plexus:end on lines %s" % (
            begin or "—", end or "—")
    block = "\n".join(lines[begin[0] - 1:end[0]])
    m = re.search(r"Managed by Plexus (\S+?)\.?\s", block)
    return "Plexus block, lines %d–%d, charter %s; %s outside it" % (
        begin[0], end[0], m.group(1) if m else "version not stated",
        many(len(lines) - (end[0] - begin[0] + 1), "line"))


def plugin_version():
    try:
        return json.load(io.open(os.path.join(HERE, "..", ".claude-plugin", "plugin.json"),
                                 encoding="utf-8")).get("version") or "version not stated"
    except (IOError, OSError, ValueError):
        return "plugin.json unreadable"


def gitignore(root):
    path = os.path.join(root, ".gitignore")
    if not os.path.isfile(path):
        return "absent"
    lines = io.open(path, encoding="utf-8", errors="replace").read().splitlines()
    try:
        b = lines.index("# plexus:begin")
        e = lines.index("# plexus:end", b)
    except ValueError:
        return "present, no Plexus lines"
    inside = [l for l in lines[b + 1:e] if l.strip()]
    return "Plexus lines: %s" % (", ".join(inside) or "none between the markers")


def personal():
    """The personal file's values that init would otherwise ask about."""
    if not os.path.isfile(PERSONAL):
        return "absent — nothing chosen yet"
    text = io.open(PERSONAL, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    # a comment is a `#` standing apart; one inside a value (`C#`) is the value's own
    found = {k: re.sub(r"(?:^|\s)#(?:\s.*)?$", "", v).strip()
             for k, v in re.findall(r"^(\w+):(.*)$", m.group(1), re.M)} if m else {}
    shown = ["%s: %s" % (k, found.get(k) or "not set") for k in ("commits", "screenshots", "tasks", "agents", "attribution")]
    return "present — " + "; ".join(shown)


def is_doc(name):
    stem, ext = os.path.splitext(name)
    return ext.lower() in DOC_EXT or stem.lower() in DOC_NAMES


def looks_like_test(rel):
    parts = rel.lower().replace("\\", "/").split("/")
    return (any(p in ("test", "tests", "spec", "specs", "__tests__") for p in parts[:-1])
            or "test" in parts[-1] or "spec" in parts[-1])


def code(root):
    found, tests = [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.startswith(".") or is_doc(name):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            found.append(rel)
            tests += looks_like_test(rel)
            if len(found) >= FILE_CAP:
                break
        if len(found) >= FILE_CAP:
            break
    if not found:
        return "none — only documents, if anything"
    count = "%d+" % FILE_CAP if len(found) >= FILE_CAP else str(len(found))
    return "%s files besides documents, %d of them look like tests; e.g. %s" % (
        count, tests, ", ".join(found[:EXAMPLES]))


def git_rows(root):
    top = git(root, "rev-parse", "--show-toplevel")
    if top is None:
        row("Git", "not a repository")
        return
    top = top.strip()
    where = "" if os.path.realpath(top) == os.path.realpath(root) else "; the repository root is %s" % top
    count = git(root, "rev-list", "--count", "HEAD")
    branch = (git(root, "branch", "--show-current") or "").strip() or "detached HEAD"
    if count is None:
        row("Git", "no commits yet, branch %s%s" % (branch, where))
    else:
        row("Git", "%s, branch %s%s" % (many(int(count), "commit"), branch, where))
    status = (git(root, "status", "--short") or "").splitlines()
    if not status:
        row("Changes", "none — the working tree is clean")
    else:
        more = " (+%d more)" % (len(status) - CHANGES) if len(status) > CHANGES else ""
        row("Changes", "%d:%s" % (len(status), more))
        for line in status[:CHANGES]:
            print("             " + line)
    remotes = (git(root, "remote", "-v") or "").split("\n")
    fetch = sorted(set("%s %s" % tuple(l.split()[:2]) for l in remotes if l.endswith("(fetch)")))
    row("Remote", ", ".join(fetch) if fetch else "none — the work stays on this machine")
    unmerged = [b.strip(" *+") for b in (git(root, "branch", "--list", "iteration/*",
                                              "--no-merged") or "").splitlines() if b.strip()]
    row("Iterations", "unmerged branches: %s" % ", ".join(unmerged) if unmerged
        else "no unmerged iteration branches")


def main(argv):
    root = os.path.abspath(argv[1] if len(argv) > 1 else os.getcwd())
    print("Ground check of %s" % root)
    for name, look in (("plexus/", lambda: plexus_dir(root)),
                       ("CLAUDE.md", lambda: charter(root)),
                       ("Plugin", plugin_version),
                       ("Defaults", personal),
                       (".gitignore", lambda: gitignore(root)),
                       ("Code", lambda: code(root))):
        try:
            row(name, look())
        except Exception as e:  # one unreadable part must not hide the rest
            row(name, "could not be read: %s" % e)
    try:
        git_rows(root)
    except Exception as e:
        row("Git", "could not be read: %s" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
