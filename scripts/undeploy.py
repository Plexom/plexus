#!/usr/bin/env python3
"""Takes Plexus out of a project in one call, as the user chose in /plexus:remove.

The reverse of deploy.py, held to the same standard: cutting a block out of
CLAUDE.md and lines out of .gitignore is the step that must leave the user's own
rules intact, so it is done by a script that checks the result and can put
everything back.

    python3 undeploy.py <project directory> --data=archive|delete|keep

    --data=archive   plexus/ becomes docs/plexus-archive/ — the spec and decisions
                     stay readable; renamed, since an installed Plexus briefs every
                     session wherever a plexus/ directory exists
    --data=delete    plexus/ is removed; it stays in the git history
    --data=keep      plexus/ stays where it is — for a plugin switched off here

What is taken: the block between <!-- plexus:begin --> and <!-- plexus:end --> in
CLAUDE.md, markers included (the file goes when nothing else was in it), and the
lines between # plexus:begin and # plexus:end in .gitignore. Everything outside the
markers stays byte for byte — the secret patterns above all, which protect the
project with or without Plexus. Branches are not touched: that is the user's word,
asked for each.

**The working tree must be clean**, so the removal is one commit that one revert
undoes. The result is checked before the commit; a failed check puts everything
back. Exit code: 0 — removed and committed; 1 — refused or rolled back, nothing
changed (reason on stderr); 2 — removed, but git could not commit.
"""

import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", ".claude-plugin", "plugin.json"))
BEGIN, END = "<!-- plexus:begin -->", "<!-- plexus:end -->"
IGNORE_BEGIN, IGNORE_END = "# plexus:begin", "# plexus:end"
ARCHIVE = os.path.join("docs", "plexus-archive")


class Refused(Exception):
    pass


class GitFailed(Exception):
    pass


def read(path):
    # newline="": line endings as they are, so what is put back is byte for byte
    with io.open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def git(root, *args):
    try:
        p = subprocess.run(["git", "-C", root] + list(args), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return p.returncode, p.stdout.strip()


def without_block(text, begin, end):
    """The text with the marked block cut out, and the blank lines it leaves joined.

    Lines are kept with their own endings, so what surrounds the block is returned
    exactly as it was. Refused unless the markers stand once each, in order: a
    broken pair cannot tell Plexus's lines from the user's.
    """
    lines = text.splitlines(True)
    b = [i for i, l in enumerate(lines) if l.strip() == begin]
    e = [i for i, l in enumerate(lines) if l.strip() == end]
    if len(b) != 1 or len(e) != 1 or e[0] < b[0]:
        raise Refused("the markers %s … %s are not there once each, in order" % (begin, end))
    before, after = lines[:b[0]], lines[e[0] + 1:]
    # the blank line deploy put before the block goes with it; one after it too
    while before and not before[-1].strip():
        before.pop()
    if before and after and not after[0].strip():
        after = after[1:]
    if before and not before[-1].endswith("\n"):
        before[-1] += "\n"
    return "".join(before + ([] if not before or not after else ["\n"]) + after)


def outside(text, begin, end):
    """The non-blank lines outside the block, to prove none of them was lost."""
    lines = text.splitlines()
    try:
        b = [l.strip() for l in lines].index(begin)
        e = [l.strip() for l in lines].index(end)
    except ValueError:
        return [l for l in lines if l.strip()]
    return [l for l in lines[:b] + lines[e + 1:] if l.strip()]


def undeploy(root, data):
    plexus = os.path.join(root, "plexus")
    archive = os.path.join(root, ARCHIVE)
    claude = os.path.join(root, "CLAUDE.md")
    ignore = os.path.join(root, ".gitignore")

    code, top = git(root, "rev-parse", "--show-toplevel")
    if code != 0:
        raise Refused("not a git repository — the removal is a commit, so it can be undone")
    code, dirty = git(root, "status", "--porcelain")
    if code != 0 or dirty:
        raise Refused("the working tree is not clean — commit first, so the removal is one "
                      "commit of its own:\n%s" % dirty)
    old_claude = read(claude) if os.path.isfile(claude) else None
    old_ignore = read(ignore) if os.path.isfile(ignore) else None
    has_block = old_claude is not None and (BEGIN in old_claude or END in old_claude)
    has_lines = old_ignore is not None and (IGNORE_BEGIN in old_ignore or IGNORE_END in old_ignore)
    if not (os.path.isdir(plexus) or has_block or has_lines):
        raise Refused("Plexus is not in this project: no plexus/, no charter block, no .gitignore lines")
    if data == "archive" and os.path.lexists(archive):
        raise Refused("%s already exists — nothing is moved over it" % ARCHIVE)

    new_claude = without_block(old_claude, BEGIN, END) if has_block else old_claude
    new_ignore = without_block(old_ignore, IGNORE_BEGIN, IGNORE_END) if has_lines else old_ignore
    version = json.load(io.open(PLUGIN, encoding="utf-8")).get("version", "")
    from plexus_state import signature  # read now: plexus/config.md is about to move
    trailer = signature(version, root)
    moved = False
    try:
        if has_block:
            if new_claude.strip():
                write(claude, new_claude)
            else:
                os.remove(claude)
        if has_lines:
            write(ignore, new_ignore)
        if os.path.isdir(plexus) and data == "archive":
            os.makedirs(os.path.dirname(archive), exist_ok=True)
            os.rename(plexus, archive)
            moved = True
        check(root, data, old_claude, old_ignore, has_block, has_lines)
    except Exception as e:
        if moved:
            os.rename(archive, plexus)
            docs = os.path.dirname(archive)
            if os.path.isdir(docs) and not os.listdir(docs):
                os.rmdir(docs)
        for path, old in ((claude, old_claude), (ignore, old_ignore)):
            if old is not None:
                write(path, old)
        raise Refused("%s — put back, nothing changed" % e)

    # deletion comes last: it is the one step a rollback could not undo, and git
    # holds the files from here on
    if os.path.isdir(plexus) and data == "delete":
        shutil.rmtree(plexus)

    print("Removed Plexus from %s" % root)
    print("  CLAUDE.md    %s" % ("untouched — no block" if not has_block else
                                 "deleted — only the charter was in it" if not os.path.isfile(claude)
                                 else "charter block removed; %d line(s) of yours kept"
                                 % len(outside(old_claude, BEGIN, END))))
    print("  .gitignore   %s" % ("Plexus lines removed; the rest kept, secret patterns included"
                                 if has_lines else "untouched — no Plexus lines"))
    print("  plexus/      %s" % {"archive": "moved to %s" % ARCHIVE, "delete": "deleted — kept in git history",
                                 "keep": "left where it is"}[data])

    paths = [p for p in ("plexus", ARCHIVE, "CLAUDE.md", ".gitignore")
             if os.path.lexists(os.path.join(root, p)) or git(root, "ls-files", "--", p)[1]]
    code, out = git(root, "add", "-A", "--", *paths)
    if code == 0:
        body = "plexus/: %s" % {"archive": "kept as documents in " + ARCHIVE, "delete": "deleted",
                                "keep": "left in place"}[data]
        code, out = git(root, "commit", "-q", "-m", "Remove Plexus\n\n%s%s" % (body, trailer),
                        "--", *paths)
    if code != 0:
        sys.stderr.write("Removed, but not committed: %s\n" % (out.splitlines()[-1] if out else "git failed"))
        return 2
    print("  git          commit %s — one revert brings it all back"
          % git(root, "rev-parse", "--short", "HEAD")[1])
    return 0


def check(root, data, old_claude, old_ignore, has_block, has_lines):
    """The result, not the fact of editing."""
    claude = os.path.join(root, "CLAUDE.md")
    if has_block and os.path.isfile(claude):
        now = read(claude)
        if BEGIN in now or END in now:
            raise Refused("CLAUDE.md still holds a marker")
        if [l for l in now.splitlines() if l.strip()] != outside(old_claude, BEGIN, END):
            raise Refused("CLAUDE.md: the lines outside the block did not survive as they were")
    if has_lines:
        now = read(os.path.join(root, ".gitignore"))
        if IGNORE_BEGIN in now or IGNORE_END in now:
            raise Refused(".gitignore still holds a marker")
        if [l for l in now.splitlines() if l.strip()] != outside(old_ignore, IGNORE_BEGIN, IGNORE_END):
            raise Refused(".gitignore: the lines outside the markers did not survive as they were")
    if data == "archive" and os.path.isdir(os.path.join(root, "plexus")):
        raise Refused("plexus/ is still there after the move")


def main(argv):
    root = os.path.abspath(argv[1] if len(argv) > 1 and not argv[1].startswith("--") else os.getcwd())
    data = [a.split("=", 1)[1] for a in argv[1:] if a.startswith("--data=")]
    try:
        if len(data) != 1 or data[0] not in ("archive", "delete", "keep"):
            raise Refused("say what happens to plexus/: --data=archive, --data=delete or --data=keep")
        return undeploy(root, data[0])
    except Refused as e:
        sys.stderr.write("Removal did not happen: %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
