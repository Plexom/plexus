#!/usr/bin/env python3
"""Replaces the charter block in CLAUDE.md with the installed version's, for /plexus:update.

The charter is a copy made at initialization, and replacing it means rewriting the
block, carrying the commit rule over and moving the user's own rules out — the same
file deploy.py writes with checks and a rollback, so it is replaced with them too. The
parts that must be exact are the script's; what is judgement — which of the old rules
are the user's — stays with the model and the user.

Two modes, from the project root:
    python3 charter.py --old
        what the old block holds that matters: its version, the commit rule, and every
        rule the installed template does not have — each a candidate for keeping;
        rules Plexus itself retired are named and dropped
    python3 charter.py [project directory]  < sections
        `=== commit rule` — the rule to carry over, as --old printed it or as settled;
        `=== below` — optional: rules the user keeps, written below the block verbatim,
        where the next update cannot overwrite them

The block is replaced where it stands; everything outside the markers is kept byte
for byte. Checked before anything is final: one block, the new version, no `{{`
left, the kept rules below it word for word. A failed check puts the file back.
Nothing is committed: the stage offers that by the commit rule.
Exit code: 0 — replaced; 1 — refused or put back (reason on stderr).
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTER = os.path.normpath(os.path.join(HERE, "..", "templates", "CLAUDE.plexus.md"))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", ".claude-plugin", "plugin.json"))
BEGIN, END = "<!-- plexus:begin -->", "<!-- plexus:end -->"
RULE = re.compile(r"^- \*\*(.+?)\.?\*\*")
# Rules Plexus itself takes out of the charter or folds into another rule or a stage.
# Found in an old block they are Plexus's, not the user's: dropped, not asked about.
# A rule Plexus retires goes on this list in the same commit.
RETIRED = set()


class Refused(Exception):
    pass


def read(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def split(text):
    """(before, block, after) around the markers, the block with both of them."""
    b, e = text.count(BEGIN), text.count(END)
    if b != 1 or e != 1 or text.index(END) < text.index(BEGIN):
        raise Refused("CLAUDE.md: the markers are not there once each, in order — "
                      "the block cannot be told from the user's lines")
    i, j = text.index(BEGIN), text.index(END) + len(END)
    return text[:i], text[i:j], text[j:]


def rules(block):
    """{title: full text} of the list items that open with a bold title."""
    found, title, lines = {}, None, []
    for line in block.replace("\r\n", "\n").split("\n"):
        m = RULE.match(line)
        if m or line.startswith("#") or line.startswith("<!--") or line.startswith("|"):
            if title:
                found[title] = "\n".join(lines).rstrip()
            title, lines = (m.group(1).strip(), [line]) if m else (None, [])
        elif title is not None:
            if line.strip():
                lines.append(line)
            else:
                found[title] = "\n".join(lines).rstrip()
                title, lines = None, []
    if title:
        found[title] = "\n".join(lines).rstrip()
    return found


def commit_rule(old_rules):
    text = old_rules.get("Commits", "")
    return re.sub(r"^- \*\*Commits\.?\*\*\s*", "", text).strip()


def show_old(root):
    path = os.path.join(root, "CLAUDE.md")
    if not os.path.isfile(path):
        raise Refused("no CLAUDE.md here")
    _, block, _ = split(read(path))
    m = re.search(r"Managed by Plexus (\S+?)\.?\s", block)
    old = rules(block)
    new = rules(read(CHARTER))
    print("Old charter: %s" % (m.group(1) if m else "version not stated"))
    print("=== commit rule")
    print(commit_rule(old) or "<none found — ask the user>")
    retired = [t for t in old if t not in new and t in RETIRED]
    extra = [t for t in old if t not in new and t not in RETIRED]
    if retired:
        print("=== retired by Plexus, dropped: %s" % ", ".join(retired))
    print("=== not in the installed template: %d" % len(extra))
    for t in extra:
        print(old[t])
        print()
    return 0


def sections(text):
    found, name, lines = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^=== (.+?)\s*$", line)
        if m:
            if name is not None:
                found[name] = "\n".join(lines).strip("\n")
            name, lines = m.group(1).strip().lower(), []
        elif name is not None:
            lines.append(line)
    if name is not None:
        found[name] = "\n".join(lines).strip("\n")
    return found


def replace(root, given):
    path = os.path.join(root, "CLAUDE.md")
    if not os.path.isfile(path):
        raise Refused("no CLAUDE.md here — /plexus:init brings Plexus in")
    rule = given.get("commit rule", "").strip()
    if not rule or "{{" in rule or re.search(r"<[^>]+>", rule):
        raise Refused("the commit rule is missing or still a placeholder")
    unknown = sorted(set(given) - {"commit rule", "below"})
    if unknown:
        raise Refused("unknown sections: %s" % ", ".join(unknown))
    below = given.get("below", "").strip()
    version = json.load(io.open(PLUGIN, encoding="utf-8")).get("version")
    if not version:
        raise Refused("no version in %s" % PLUGIN)

    old = read(path)
    before, _, after = split(old)
    nl = "\r\n" if "\r\n" in old else "\n"
    lines = rule.splitlines()
    rule = "\n".join([lines[0]] + ["  " + l.strip() if l.strip() else "" for l in lines[1:]])
    block = (read(CHARTER).rstrip("\n").replace("{{VERSION}}", version)
             .replace("{{COMMIT_RULE}}", rule).replace("\n", nl))
    kept = (nl + nl + below.replace("\n", nl)) if below else ""
    new = before + block + kept + after
    write(path, new)
    try:
        now = read(path)
        b, inside, a = split(now)
        if "{{" in inside:
            raise Refused("a placeholder is left between the markers")
        if "Managed by Plexus %s." % version not in inside:
            raise Refused("the charter does not carry version %s" % version)
        if b != before or not a.endswith(after):
            raise Refused("what was outside the block did not survive as it was")
        for line in below.splitlines():
            if line.strip() and line.strip() not in [l.strip() for l in a.splitlines()]:
                raise Refused("a kept rule is not below the block word for word: %s" % line.strip()[:60])
    except Exception as e:
        write(path, old)
        raise Refused("%s — put back, nothing changed" % e)
    print("Charter replaced: Plexus %s" % version)
    print("  commit rule  carried over")
    print("  below        %s" % ("%d line(s) of kept rules, outside the markers" % len(below.splitlines())
                                 if below else "nothing added"))
    print("Checked: one block, version %s, no {{ left, the lines outside it as they were." % version)
    return 0


def main(argv):
    try:
        if len(argv) > 1 and argv[1] == "--old":
            return show_old(os.getcwd())
        root = os.path.abspath(argv[1] if len(argv) > 1 else os.getcwd())
        return replace(root, sections(sys.stdin.read()))
    except Refused as e:
        sys.stderr.write("The charter was not replaced: %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
