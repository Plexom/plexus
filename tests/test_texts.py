#!/usr/bin/env python3
"""The texts the model reads, kept from drifting: one home per rule, and a size budget.

A fix added where its symptom showed, rather than where its rule lives, copies the rule
into one more skill, and copies drift apart. These checks make that visible at once.

When one fails: find the rule's home and edit it there, or move what only one stage needs
into that stage's references/. Raise a budget only knowingly, in a commit that says why.
    python3 -m unittest discover -s tests
"""

import glob
import io
import os
import re
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CHARTER = os.path.join(ROOT, "templates", "CLAUDE.plexus.md")
SKILLS = sorted(glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md")))
REFERENCES = sorted(glob.glob(os.path.join(ROOT, "skills", "*", "references", "*.md")))

# Words. The charter is loaded into every session of every project; a skill, every time
# its stage runs.
CHARTER_BUDGET = 1300
SKILL_BUDGET = 2700
ALL_BUDGET = 22000

# A phrase that carries a rule, and the one file allowed to hold it. Elsewhere the
# rule is referred to by name — "by the rule on screenshots in CLAUDE.md".
HOMES = {
    "I check this myself from now on": "templates/CLAUDE.plexus.md",
    "plexus-shots/": "templates/CLAUDE.plexus.md",
    "never `git commit` directly": "templates/CLAUDE.plexus.md",
    "marked \"(Recommended)\"": "templates/CLAUDE.plexus.md",
    "is put back in your words": "templates/CLAUDE.plexus.md",
    "one unambiguous, brief document": "templates/CLAUDE.plexus.md",
    "The number of files is not a measure": "skills/plan/SKILL.md",
}


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def body(path):
    """The text without its front matter: a skill's description repeats "In a project
    with plexus/" on purpose — each must stand alone when Claude Code picks a skill."""
    text = read(path)
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def words(text):
    return len(text.split())


def sentences(text):
    flat = re.sub(r"\s+", " ", text)
    return {s.strip() for s in re.split(r"(?<=[.!?;:])\s+", flat) if len(s.split()) >= 15}


def rel(path):
    return os.path.relpath(path, ROOT)


class Budget(unittest.TestCase):
    def test_the_charter_stays_small(self):
        n = words(read(CHARTER))
        self.assertLessEqual(n, CHARTER_BUDGET, "the charter has %d words; it is read in "
                             "every session — move what one stage needs into that stage" % n)

    def test_each_skill_stays_within_its_budget(self):
        for path in SKILLS:
            n = words(read(path))
            self.assertLessEqual(n, SKILL_BUDGET, "%s has %d words — what does it repeat, "
                                 "and what does only one of its runs need?" % (rel(path), n))

    def test_the_whole_stays_within_its_budget(self):
        n = sum(words(read(p)) for p in [CHARTER] + SKILLS + REFERENCES)
        self.assertLessEqual(n, ALL_BUDGET, "charter, skills and references: %d words" % n)


class OneHome(unittest.TestCase):
    def test_no_long_sentence_is_written_twice(self):
        seen = {}
        for path in [CHARTER] + SKILLS + REFERENCES:
            for s in sentences(body(path)):
                seen.setdefault(s, []).append(rel(path))
        twice = ["%s — %s" % (", ".join(where), s[:100])
                 for s, where in seen.items() if len(where) > 1]
        self.assertEqual(twice, [], "a sentence copied between texts drifts apart from its "
                         "copy; keep it in one and refer to it:\n" + "\n".join(twice))

    def test_each_rule_lives_in_its_home(self):
        for phrase, home in HOMES.items():
            found = [rel(p) for p in [CHARTER] + SKILLS + REFERENCES if phrase in body(p)]
            self.assertEqual(found, [home], "%r belongs in %s only" % (phrase, home))

    def test_retired_rules_are_not_in_the_charter(self):
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import charter
        titles = set(charter.rules(read(CHARTER)))
        self.assertEqual(titles & charter.RETIRED, set(),
                         "a retired rule is back in the charter: take it off RETIRED in "
                         "charter.py, or the update drops it from every project")


if __name__ == "__main__":
    unittest.main()
