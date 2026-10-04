#!/usr/bin/env python3
"""Deploys Plexus into a project in one call, from what init settled with the user.

Everything init leaves behind is written here, at once: plexus/ with the
spec, the configuration and the state; the charter block in CLAUDE.md; the
lines in .gitignore; the answers that belong to the person, in their personal
file; and the first commit — in a repository created here if there is none,
because from implementation on the route runs on commits and branches. By hand
it would be five or six tool calls, each asking the user's permission, and the
part easiest to simplify — the .gitignore markers /plexus:remove relies on —
the easiest to lose. Here it is one command, and the parts that must be exact
are not the model's to write.

The texts of the three plexus/ files come from the model, in the language of
the conversation — a script cannot translate. The rest the script fills itself:
the charter's version from plugin.json, the markers, the secret patterns.

Two modes:
    python3 deploy.py --templates
        prints the three templates, each under a `=== <name>` line — exactly the
        format the deployment reads back; and the charter too, when ./CLAUDE.md
        exists, since a charter appended to someone's rules is compared first
    python3 deploy.py <project directory> [options]  < sections
        reads from stdin the sections `=== spec/index.md`, one `=== spec/<part>.md`
        per part of the product, `=== config.md`, `=== state.md` and
        `=== commit rule`, and deploys; a project with code
        adds what its reading found — `=== iterations/00-before-plexus.md`,
        `=== decisions/…`, `=== backlog.md` — any .md path inside plexus/

Options:
    --screenshots=allowed | --screenshots=not-allowed
        the user's answer, written into ~/.claude/plexus/defaults.md: it is
        permission to capture their screen, not a property of the project
    --in-parent-repo
        the project sits inside a repository whose root is above it, and the user
        agreed that the first commit goes there; without it that case is refused

**Checks the input before writing and the result after.** Refused input writes
nothing; a failed result is rolled back — plexus/ removed, CLAUDE.md and
.gitignore restored byte for byte — so a retry never meets "already exists".
Git comes last and only commits Plexus's own paths — nothing of the user's that
happens to be staged or changed goes into that commit.
Exit code: 0 — deployed and committed; 1 — refused or rolled back, nothing is
left (reason on stderr); 2 — deployed, but git could not commit (the files stay,
the reason and the fix are on stderr).
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.normpath(os.path.join(HERE, "..", "templates", "plexus"))
CHARTER = os.path.normpath(os.path.join(HERE, "..", "templates", "CLAUDE.plexus.md"))
PLUGIN = os.path.normpath(os.path.join(HERE, "..", ".claude-plugin", "plugin.json"))
FILES = ["spec/index.md", "config.md", "state.md"]
PART = "spec/_part.md"  # the template a part of the spec is written from
RULE = "commit rule"
BEGIN, END = "<!-- plexus:begin -->", "<!-- plexus:end -->"
# they protect the project with or without Plexus, so they go outside the markers
# and /plexus:remove never takes them back
# `!.env.example` after `.env.*`: the example file holds no secrets and is meant to be shared
SECRETS = [".env", ".env.*", "!.env.example", "*.pem", "*.key"]
# a person's own Claude Code settings — the rule that lets Plexus edit plexus/ lives there;
# outside the markers too, since it is theirs with or without Plexus
LOCAL = [".claude/settings.local.json"]
IGNORED = ["plexus/dashboard.html"]
PERSONAL = os.path.join(os.path.expanduser("~"), ".claude", "plexus", "defaults.md")
PERSONAL_TEMPLATE = os.path.normpath(os.path.join(HERE, "..", "templates", "defaults.md"))
SCREENSHOTS = {"allowed": "allowed", "not-allowed": "not allowed"}


class GitFailed(Exception):
    pass


class Refused(Exception):
    pass


def read(path):
    return io.open(path, encoding="utf-8").read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def templates(root):
    for name in FILES:
        print("=== %s" % name)
        print(read(os.path.join(TEMPLATES, name)).rstrip("\n"))
        if name == "spec/index.md":
            print("=== spec/<part>.md — one per part of the product, named in its own words")
            print(read(os.path.join(TEMPLATES, PART)).rstrip("\n"))
    print("=== %s" % RULE)
    print("<the commit rule settled with the user; their words quoted beneath when reworded>")
    if os.path.isfile(os.path.join(root, "CLAUDE.md")):
        print("\n--- charter, for comparison with the existing CLAUDE.md: the script writes it "
              "itself, do not send it back ---")
        print(read(CHARTER).rstrip("\n"))
    return 0


def sections(text):
    found, name, lines = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^=== (.+?)\s*$", line)
        if m:
            if name is not None:
                found[name] = "\n".join(lines).strip("\n") + "\n"
            name, lines = m.group(1).strip().lower(), []
        elif name is not None:
            lines.append(line)
    if name is not None:
        found[name] = "\n".join(lines).strip("\n") + "\n"
    return found


NOTE = re.compile(r"[ \t]*<!-- template:.*?-->[ \t]*\n?", re.S)


def without_notes(text):
    """The text without the templates' notes to the writer: they guide the one who fills
    the template and are not part of the project's document."""
    return re.sub(r"\n{3,}", "\n\n", NOTE.sub("", text))


def placeholders():
    """Every `<...>` the templates hold, whitespace collapsed.

    Only these count as unfilled: a user's own words may hold angle brackets — a
    greeting that prints «Привет, <имя>!», a tag, a command's argument — and a check
    that took any `<...>` for a placeholder would push the agent to rewrite the user's text.
    """
    found = set()
    for folder, _, names in os.walk(TEMPLATES):
        for name in names:
            if name.endswith(".md"):
                for m in re.finditer(r"<[^<>!][^<>]*>", read(os.path.join(folder, name))):
                    found.add(" ".join(m.group(0).split()))
    return found


def leftover(text, known=None):
    """A template placeholder left in prose or in the header, or None.

    Rows of tables are left out: a row with `<...>` is the template's example of
    the format, the scripts skip it as not data, and discovery replaces it. In
    prose and in the header a placeholder is a question nobody answered — it
    reads as noise, or as a stage name the user has never heard of.
    """
    known = placeholders() if known is None else known
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)  # notes and anchors, not placeholders
    prose = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("|"))
    for m in re.finditer(r"<[^<>!][^<>]*>", prose):
        spot = " ".join(m.group(0).split())
        if spot in known:
            return spot[:80]
    return None


def header(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    # a comment is a `#` standing apart; one inside a value (`stack: C#`) is the value's own
    return {k: re.sub(r"(?:^|\s)#(?:\s.*)?$", "", v).strip()
            for k, v in re.findall(r"^(\w+):(.*)$", m.group(1), re.M)}


def extra(name):
    """A further file inside plexus/, as a project with code has: a relative .md path."""
    parts = name.split("/")
    return (name not in FILES + [RULE] and name.endswith(".md") and not name.startswith("/")
            and all(re.match(r"^[\w.-]+$", p) and p not in (".", "..") for p in parts))


def check_input(given):
    missing = [n for n in FILES + [RULE] if not given.get(n, "").strip()]
    if missing:
        raise Refused("sections missing or empty: %s" % ", ".join(missing))
    if not [n for n in given if n.startswith("spec/") and n != "spec/index.md"]:
        # the front page lists the parts; the parts hold what the product does
        raise Refused("the spec has no parts: at least one `=== spec/<part>.md` besides the index")
    unknown = sorted(n for n in given if n not in FILES + [RULE] and not extra(n))
    if unknown:
        raise Refused("unknown sections: %s — a file goes as a .md path inside plexus/"
                      % ", ".join(unknown))
    known = placeholders()
    for name in [n for n in given if n != RULE]:
        spot = leftover(given[name], known)
        if spot:
            raise Refused("%s still holds a template placeholder: %s — write what is known, "
                          "or that it will be filled in the next step" % (name, spot))
    for name in ("config.md", "state.md"):
        if header(given[name]) is None:
            raise Refused("%s has no header between --- lines; the scripts read it" % name)
    if header(given["state.md"]).get("stage") != "init":
        raise Refused("state.md: `stage` must be `init` — this deployment is init's")
    if "{{" in given[RULE]:
        raise Refused("the commit rule holds a {{placeholder}}")


def charter_block(rule):
    version = json.load(io.open(PLUGIN, encoding="utf-8")).get("version")
    if not version:
        raise Refused("no version in %s" % PLUGIN)
    lines = rule.strip("\n").splitlines()
    # the rule sits in a list item: its later lines, the user's words among them,
    # are indented to stay inside that item
    rule = "\n".join([lines[0]] + ["  " + l.strip() if l.strip() else "" for l in lines[1:]])
    return read(CHARTER).replace("{{VERSION}}", version).replace("{{COMMIT_RULE}}", rule), version


def spec_summary(root):
    """What the spec holds, counted the way the stages will count it."""
    sys.path.insert(0, HERE)
    import pathlib
    from plexus_state import tagged_items, table_rows
    folder = pathlib.Path(root) / "plexus" / "spec"
    parts = sorted(p for p in folder.glob("*.md") if p.name != "index.md" and not p.name.startswith("_"))
    features = [i for p in parts for i in tagged_items(p) if i[0].startswith("feature-")]
    first = sum(1 for i in features if i[1] == "mvp")
    constraints = len(table_rows(folder / "index.md", "constraint"))
    def n(count, word):
        return "%d %s%s" % (count, word, "" if count == 1 else "s")
    return "Spec: %s in %s (%d in the first version), %s" % (
        n(len(features), "feature"), n(len(parts), "part"), first, n(constraints, "always-true constraint"))


def git(root, *args):
    try:
        p = subprocess.run(["git", "-C", root] + list(args), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return p.returncode, p.stdout.strip()


def repository(root, in_parent):
    """The repository the first commit goes into — checked before anything is written.

    A project inside someone's larger repository (a home folder under version
    control, a monorepo) must not get a commit there by surprise.
    """
    code, top = git(root, "rev-parse", "--show-toplevel")
    if code != 0:
        return None  # none yet — created after the files are in place
    if os.path.realpath(top) != os.path.realpath(root) and not in_parent:
        raise Refused("the project is inside the repository %s — ask the user whether the "
                      "first commit goes there, then pass --in-parent-repo" % top)
    return top


def commit(root, version, created):
    if created:
        code, out = git(root, "init", "-q")
        if code != 0:
            raise GitFailed("git init failed: %s" % out)
    paths = ["plexus", "CLAUDE.md", ".gitignore"]
    code, out = git(root, "add", "--", *paths)
    if code != 0:
        raise GitFailed("git add failed: %s" % out)
    # the paths after -- keep this commit to Plexus's files, whatever else is staged
    from plexus_state import signature
    message = "Plexus %s: init%s" % (version, signature(version, root))
    code, out = git(root, "commit", "-q", "-m", message, "--", *paths)
    if code != 0:
        hint = (" — git does not know who commits yet: ask the user for the name and email "
                "to sign commits with, set them for this repository only (git config user.name, "
                "git config user.email), then commit plexus/, CLAUDE.md and .gitignore"
                if "user.email" in out or "identity" in out.lower() else "")
        raise GitFailed("git commit failed: %s%s" % (out.splitlines()[-1] if out else "", hint))
    return git(root, "rev-parse", "--short", "HEAD")[1]


def set_personal(key, value):
    """One value in the personal file's header, the file created from its template if absent."""
    if not os.path.isfile(PERSONAL):
        os.makedirs(os.path.dirname(PERSONAL), exist_ok=True)
        shutil.copyfile(PERSONAL_TEMPLATE, PERSONAL)
    text = read(PERSONAL)
    new, n = re.subn(r"^(%s:)[^\S\n]*[^#\n]*?(\s*#.*)?$" % key,
                     lambda m: "%s %s%s" % (m.group(1), value, m.group(2) or ""), text, count=1,
                     flags=re.M)
    if n != 1:
        raise IOError("no `%s:` line in %s" % (key, PERSONAL))
    write(PERSONAL, new)


def deploy(root, given, screenshots=None, in_parent=False):
    target = os.path.join(root, "plexus")
    claude = os.path.join(root, "CLAUDE.md")
    ignore = os.path.join(root, ".gitignore")
    if os.path.lexists(target):
        raise Refused("%s already exists — the state in it is the project's work" % target)
    old_claude = read(claude) if os.path.isfile(claude) else None
    old_ignore = read(ignore) if os.path.isfile(ignore) else None
    if old_claude is not None and (BEGIN in old_claude or END in old_claude):
        raise Refused("CLAUDE.md already has Plexus markers — /plexus:update is for that")
    if old_ignore is not None and "# plexus:begin" in old_ignore:
        raise Refused(".gitignore already has Plexus lines")
    block, version = charter_block(given[RULE])
    repo = repository(root, in_parent)

    new_claude = block if old_claude is None else old_claude.rstrip("\n") + "\n\n" + block
    present = set(l.strip() for l in (old_ignore or "").splitlines())
    secrets = [p for p in SECRETS if p not in present]
    local = [p for p in LOCAL if p not in present]
    tail = []
    if secrets:
        tail += ["# Secrets"] + secrets + [""]
    if local:
        tail += ["# Personal Claude Code settings"] + local + [""]
    tail += ["# plexus:begin"] + IGNORED + ["# plexus:end"]
    base = (old_ignore or "").rstrip("\n")
    new_ignore = (base + "\n\n" if base else "") + "\n".join(tail) + "\n"

    try:
        os.makedirs(target)
        for name in [n for n in given if n != RULE]:
            path = os.path.join(target, *name.split("/"))
            if not os.path.isdir(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            write(path, given[name])
        write(claude, new_claude)
        write(ignore, new_ignore)
        verify(root, given, version, old_claude, old_ignore)
    except Exception as e:
        # plexus/ is ours — created a few lines above; the other two go back to
        # exactly what they were, or away if they were not there
        shutil.rmtree(target, ignore_errors=True)
        for path, old in ((claude, old_claude), (ignore, old_ignore)):
            try:
                if old is None:
                    if os.path.exists(path):
                        os.remove(path)
                else:
                    write(path, old)
            except (IOError, OSError):
                pass
        raise Refused("%s — rolled back, nothing is left" % e)

    print("Deployed Plexus %s into %s" % (version, root))
    print("  plexus/      %s" % ", ".join(n for n in given if n != RULE))
    print("  CLAUDE.md    %s" % ("created with the charter" if old_claude is None else
                                 "charter appended; what was above it untouched (%d line%s)"
                                 % (len(old_claude.rstrip("\n").splitlines()),
                                    "" if len(old_claude.rstrip("\n").splitlines()) == 1 else "s")))
    print("  .gitignore   %s; Plexus lines between # plexus:begin and # plexus:end%s" % (
        "created" if old_ignore is None else "appended",
        "; secret patterns added outside them: %s" % " ".join(secrets) if secrets else ""))
    print("  %s" % spec_summary(root))
    print("Checked: every file in place, the charter's markers once, no {{ left, "
          "the .gitignore markers, the lines that were there before kept.")
    if screenshots:
        try:
            set_personal("screenshots", screenshots)
            print("  personal     screenshots: %s — in %s" % (screenshots, PERSONAL))
        except (IOError, OSError) as e:
            # the project is deployed; a personal answer not written is asked again later
            print("  personal     screenshots NOT written: %s" % e)
    try:
        sha = commit(root, version, repo is None)
    except GitFailed as e:
        sys.stderr.write("Deployed, but not committed: %s\n" % e)
        return 2
    print("  git          %s; commit %s with Plexus's files only" % (
        "repository created" if repo is None else "existing repository", sha))
    return 0


def verify(root, given, version, old_claude, old_ignore):
    """The result, not the fact of writing."""
    for name in [n for n in given if n != RULE]:
        if read(os.path.join(root, "plexus", *name.split("/"))) != given[name]:
            raise Refused("plexus/%s does not hold what was written" % name)
    claude = read(os.path.join(root, "CLAUDE.md"))
    if claude.count(BEGIN) != 1 or claude.count(END) != 1:
        raise Refused("CLAUDE.md: the markers are not there exactly once")
    inside = claude[claude.index(BEGIN):claude.index(END)]
    if "{{" in inside:
        raise Refused("CLAUDE.md: a placeholder is left between the markers")
    if "Managed by Plexus %s." % version not in inside:
        raise Refused("CLAUDE.md: the charter does not carry version %s" % version)
    if old_claude is not None and not claude.startswith(old_claude.rstrip("\n")):
        raise Refused("CLAUDE.md: what was there before did not survive")
    ignore = read(os.path.join(root, ".gitignore")).splitlines()
    if ignore.count("# plexus:begin") != 1 or ignore.count("# plexus:end") != 1:
        raise Refused(".gitignore: the markers are not there exactly once")
    between = ignore[ignore.index("# plexus:begin") + 1:ignore.index("# plexus:end")]
    if between != IGNORED:
        raise Refused(".gitignore: the lines between the markers are not Plexus's")
    if old_ignore is not None and ignore[:len(old_ignore.splitlines())] != old_ignore.splitlines():
        raise Refused(".gitignore: the lines that were there before did not survive")


def main(argv):
    if len(argv) > 1 and argv[1] == "--templates":
        return templates(os.getcwd())
    root = os.path.abspath(argv[1] if len(argv) > 1 else os.getcwd())
    try:
        if not os.path.isdir(root):
            raise Refused("no such project directory: %s" % root)
        for path in [os.path.join(TEMPLATES, n) for n in FILES + [PART]] + [CHARTER, PLUGIN]:
            if not os.path.isfile(path):
                raise Refused("the plugin is missing %s" % path)
        options = argv[2:]
        screenshots = None
        for o in options:
            if o.startswith("--screenshots="):
                screenshots = SCREENSHOTS.get(o.split("=", 1)[1])
                if screenshots is None:
                    raise Refused("--screenshots takes allowed or not-allowed")
            elif o != "--in-parent-repo":
                raise Refused("unknown option: %s" % o)
        given = {n: (t if n == RULE else without_notes(t))
                 for n, t in sections(sys.stdin.read()).items()}
        check_input(given)
        return deploy(root, given, screenshots, "--in-parent-repo" in options)
    except Refused as e:
        sys.stderr.write("Deployment did not happen: %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
