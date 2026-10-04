#!/usr/bin/env python3
"""The templates a stage creates its files from, printed into the stage itself.

A stage that writes a decision, a task or a design creates the file from the plugin's
template. Read by the model, that template lives outside the project, and every read
asks the user's permission — at every stage, for the same few files. Printed here
through the stage's own `!` block, it arrives with the stage's instructions and asks
nothing.

Run from the project root:
    python3 templates.py <name> [<name> …]
    names: decision, research, iteration, task, design, backlog, changelog, architecture,
           spec — the front page and the part template; charter — the CLAUDE.md block,
           existing-code — init's reference for a project with code, with the templates
           it writes from; printed only when the project has code
Exit code: 0, always — an unknown name is said in its own line.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PLEXUS = os.path.join(ROOT, "templates", "plexus")
FILES = {
    "decision": "decisions/_template.md",
    "research": "research/_template.md",
    "iteration": "iterations/_template.md",
    "task": "tasks/_template.md",
    "design": "design.md",
    "backlog": "backlog.md",
    "changelog": "changelog.md",
    "spec": "spec/index.md",
    "architecture": "architecture.md",
}
CHARTER = os.path.join(ROOT, "templates", "CLAUDE.plexus.md")
EXISTING = os.path.join(ROOT, "skills", "init", "references", "existing-code.md")


def show(title, path):
    print("=== %s" % title)
    print(io.open(path, encoding="utf-8").read().rstrip("\n"))
    print()


def has_code(root):
    sys.path.insert(0, HERE)
    from ground import code, git  # one idea of "code is here", shared with the ground check
    commits = (git(root, "rev-list", "--count", "HEAD") or "0").strip()
    return not code(root).startswith("none") or int(commits or 0) > 2


def main(argv):
    for name in argv[1:]:
        if name == "existing-code":
            if not has_code(os.getcwd()):
                print("[no code here — the reference for a project with code is not needed]")
                continue
            show("init: a project with code", EXISTING)
            for t in ("iteration", "decision", "backlog", "architecture"):
                show("plexus/" + FILES[t], os.path.join(PLEXUS, FILES[t]))
        elif name == "charter":
            show("CLAUDE.md block — templates/CLAUDE.plexus.md", CHARTER)
        elif name in FILES:
            show("plexus/" + FILES[name], os.path.join(PLEXUS, FILES[name]))
            if name == "spec":
                show("plexus/spec/<part>.md", os.path.join(PLEXUS, "spec", "_part.md"))
        else:
            print("[no template named %s]" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
