#!/usr/bin/env python3
"""Every commit Plexus makes, signed by code rather than by memory.

A rule kept only in text is forgotten exactly where a commit is made in passing — a
stage's own commit after plan, design or verify. So the `Built-with` line is added
here, or left out where `attribution: off` stands, whoever commits.

From the project root, the message on stdin — a heredoc keeps backticks and quotes as
they are:
    python3 commit.py [path ...] <<'MSG'
    plan: iteration-03 · records and the new word, 6 tasks
    MSG
With paths, exactly those are added and committed, whatever else is staged — a stage
commits what it changed and never the user's unrelated edits. Without paths, what is
already staged.
Exit code: 0 — committed, the short hash printed; 1 — nothing to commit or no message;
2 — git refused (its words printed, with what to do about a missing identity).
"""

import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", ".claude-plugin", "plugin.json"))


def git(*args):
    try:
        p = subprocess.run(["git"] + list(args), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return p.returncode, p.stdout.strip()


def main(argv):
    paths = argv[1:]
    message = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8").read().strip()
    if not message:
        print("no message on stdin", file=sys.stderr)
        return 1
    if "\nBuilt-with:" not in "\n" + message:
        from plexus_state import signature
        version = json.load(io.open(PLUGIN, encoding="utf-8")).get("version", "")
        message += signature(version, ".")
    if paths:
        code, out = git("add", "--", *paths)
        if code != 0:
            print("git add failed: %s" % out, file=sys.stderr)
            return 2
        code, _ = git("diff", "--cached", "--quiet", "--", *paths)
    else:
        code, _ = git("diff", "--cached", "--quiet")
    if code == 0:
        print("nothing to commit%s" % (" in " + " ".join(paths) if paths else " — nothing staged; "
              "name the paths this step changed"), file=sys.stderr)
        return 1
    # the paths after -- keep the commit to them, whatever else is staged
    p = subprocess.run(["git", "commit", "-q", "-F", "-"] + (["--"] + paths if paths else []),
                       input=message, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, encoding="utf-8")
    if p.returncode != 0:
        out = p.stdout.strip()
        hint = (" — git does not know who commits yet: ask the user for the name and email to "
                "sign commits with, and set them for this repository only (git config "
                "user.name, git config user.email)"
                if "user.email" in out or "identity" in out.lower() else "")
        print("git commit failed: %s%s" % (out.splitlines()[-1] if out else "", hint),
              file=sys.stderr)
        return 2
    print("commit %s · %s" % (git("rev-parse", "--short", "HEAD")[1], message.splitlines()[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
