#!/usr/bin/env python3
"""The scripts' behaviour, pinned: most tests keep a bug from coming back.

Deterministic and free: run it after any change to scripts/.
    python3 -m unittest discover -s tests
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


VERSION = json.loads(read(os.path.join(ROOT, ".claude-plugin", "plugin.json")))["version"]

SPEC = u"""# Продукт

## Что мы строим

> тетрис, `feature-09` здесь только ссылка

## Очистка линий

- Слово появляется на месте ряда. `feature-01 · MVP`
- Слова идут по кругу; пустой список —
  берётся следующий. `feature-02 · later`
- <что продукт делает> `feature-03 · MVP`

## Что важно всегда

| id | что | как проверяем |
|---|---|---|
| constraint-01 | Без интернета | открыть без сети |
"""

CLEAN_SPEC = SPEC.replace(u"- <что продукт делает> `feature-03 · MVP`\n", u"")

INDEX = u"""# Тетрис

## Что мы строим

> тетрис в браузере

## Части

| часть | файл | что охватывает |
|---|---|---|
| Игра | [game.md](game.md) | правила и очистка линий |
"""

SECTIONS = u"""=== spec/index.md
""" + INDEX + u"""=== spec/game.md
%s=== config.md
---
stack:
research: off
parallel: not checked
---

# Конфигурация
=== state.md
---
stage: init
next: discover
---

# Состояние
=== commit rule
Commit without asking.
"""


def write(path, text):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run(args, cwd, stdin=None, home=None):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    if home:
        env["HOME"] = home
    p = subprocess.run([sys.executable] + args, cwd=cwd, input=stdin, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return p.returncode, p.stdout, p.stderr


class Tmp(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.home = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)


class ReadableSpec(Tmp):
    def features(self):
        os.makedirs(os.path.join(self.dir, "plexus", "spec"))
        write(os.path.join(self.dir, "plexus", "spec", "index.md"), INDEX)
        write(os.path.join(self.dir, "plexus", "spec", "game.md"), SPEC)
        code, out, _ = run([os.path.join(SCRIPTS, "tables.py"), "features", "--all"], self.dir)
        return code, out

    def test_tagged_items_are_features(self):
        code, out = self.features()
        self.assertIn("feature-01", out)
        self.assertIn(u"берётся следующий", out)  # the wrapped line belongs to its item
        self.assertIn("later", out)

    def test_a_reference_mid_sentence_is_not_a_definition(self):
        self.assertNotIn("feature-09", self.features()[1])

    def test_a_template_example_is_not_a_feature(self):
        self.assertNotIn("feature-03", self.features()[1])

    def test_each_feature_names_its_part(self):
        self.assertIn("game", self.features()[1])

    def test_one_id_in_two_parts_is_reported(self):
        self.features()
        write(os.path.join(self.dir, "plexus", "spec", "rules.md"), u"- Другое. `feature-01 · MVP`\n")
        code, _, err = run([os.path.join(SCRIPTS, "tables.py"), "features"], self.dir)
        self.assertEqual(code, 2)
        self.assertIn("feature-01 is defined here and in game.md", err)


class Deploy(Tmp):
    def deploy(self, spec=CLEAN_SPEC, extra=()):
        return run([os.path.join(SCRIPTS, "deploy.py"), "."] + list(extra), self.dir,
                   stdin=SECTIONS % spec, home=self.home)

    def test_deploys_and_commits_only_plexus_files(self):
        write(os.path.join(self.dir, "mine.txt"), u"x")
        code, out, err = self.deploy()
        self.assertEqual(code, 0, err)
        tracked = subprocess.run(["git", "ls-files"], cwd=self.dir, stdout=subprocess.PIPE,
                                 universal_newlines=True).stdout.split()
        self.assertNotIn("mine.txt", tracked)
        self.assertIn("CLAUDE.md", tracked)
        gitignore = read(os.path.join(self.dir, ".gitignore"))
        self.assertIn("# plexus:begin", gitignore)  # remove relies on the markers

    def last_message(self):
        return subprocess.run(["git", "log", "-1", "--format=%B"], cwd=self.dir,
                              stdout=subprocess.PIPE, universal_newlines=True).stdout

    def test_the_first_commit_is_signed(self):
        self.assertEqual(self.deploy()[0], 0)
        self.assertIn("\n\nBuilt-with: Plexus %s" % VERSION, self.last_message())
        charter = read(os.path.join(self.dir, "CLAUDE.md"))
        self.assertIn("never `git commit` directly", charter)

    def test_the_signature_is_left_out_where_the_person_said_off(self):
        os.makedirs(os.path.join(self.home, ".claude", "plexus"))
        write(os.path.join(self.home, ".claude", "plexus", "defaults.md"),
              u"---\nattribution: off   # on | off\n---\n")
        self.assertEqual(self.deploy()[0], 0)
        self.assertNotIn("Built-with", self.last_message())

    def test_a_spec_without_parts_is_refused(self):
        code, _, err = run([os.path.join(SCRIPTS, "deploy.py"), "."], self.dir,
                           stdin=(SECTIONS % CLEAN_SPEC).replace(u"=== spec/game.md\n", u""), home=self.home)
        self.assertEqual(code, 1)
        self.assertIn("no parts", err)

    def test_a_placeholder_in_prose_is_refused_and_nothing_written(self):
        code, _, err = self.deploy(spec=CLEAN_SPEC.replace(u"## Очистка линий", u"## <The part's name, in its own words>"))
        self.assertEqual(code, 1)
        self.assertIn("placeholder", err)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "plexus")))

    def test_angle_brackets_of_the_users_own_are_not_a_placeholder(self):
        # refused, «печатает „Привет, <имя>!“» would push the agent to rewrite the user's
        # words to get past the check
        code, _, err = self.deploy(spec=CLEAN_SPEC.replace(u"## Очистка линий",
                                                            u"## Очистка линий\n\nПечатает «Привет, <имя>!»."))
        self.assertEqual(code, 0, err)

    def test_the_templates_notes_are_not_written_into_the_project(self):
        note = u"<!-- template:\nThe spec's front page: what the product is.\n-->\n\n"
        code, _, err = self.deploy(spec=note + CLEAN_SPEC)
        self.assertEqual(code, 0, err)
        written = read(os.path.join(self.dir, "plexus", "spec", "game.md"))
        self.assertNotIn("template:", written)
        self.assertNotIn("front page", written)

    def test_a_repository_above_the_project_is_not_committed_into_silently(self):
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        sub = os.path.join(self.dir, "sub")
        os.makedirs(sub)
        code, _, err = run([os.path.join(SCRIPTS, "deploy.py"), "."], sub, stdin=SECTIONS % CLEAN_SPEC,
                           home=self.home)
        self.assertEqual(code, 1)
        self.assertIn("--in-parent-repo", err)


    def test_the_example_env_file_is_not_hidden_from_git(self):
        self.assertEqual(self.deploy()[0], 0)
        ignored = lambda name: subprocess.run(["git", "check-ignore", "-q", name],
                                              cwd=self.dir).returncode == 0
        self.assertTrue(ignored(".env.local"))
        self.assertTrue(ignored(".claude/settings.local.json"))  # the plexus/ edit rule lives there
        self.assertFalse(ignored(".env.example"))


class Commit(Tmp):
    """Every Plexus commit goes through commit.py, so a stage's own commit, made in
    passing, carries the signature too."""

    def setUp(self):
        Tmp.setUp(self)
        os.makedirs(os.path.join(self.dir, "plexus"))
        write(os.path.join(self.dir, "plexus", "state.md"), u"x\n")
        write(os.path.join(self.dir, "mine.txt"), u"the user's own edit\n")
        subprocess.run(["git", "init", "-q"], cwd=self.dir)

    def commit(self, *paths, **kw):
        return run([os.path.join(SCRIPTS, "commit.py")] + list(paths), self.dir,
                   stdin=kw.get("message", u"plan: `iteration-03` · records\n"), home=self.home)

    def message(self):
        return subprocess.run(["git", "log", "-1", "--format=%B"], cwd=self.dir,
                              stdout=subprocess.PIPE, universal_newlines=True).stdout

    def test_signs_and_commits_only_the_named_paths(self):
        code, out, err = self.commit("plexus")
        self.assertEqual(code, 0, err)
        self.assertIn("plan: `iteration-03` · records\n\nBuilt-with: Plexus %s" % VERSION,
                      self.message())
        tracked = subprocess.run(["git", "ls-files"], cwd=self.dir, stdout=subprocess.PIPE,
                                 universal_newlines=True).stdout.split()
        self.assertEqual(tracked, ["plexus/state.md"])

    def test_off_in_the_project_leaves_the_line_out(self):
        write(os.path.join(self.dir, "plexus", "config.md"), u"---\nattribution: off\n---\n")
        self.assertEqual(self.commit("plexus")[0], 0)
        self.assertNotIn("Built-with", self.message())

    def test_a_signed_message_is_not_signed_twice(self):
        self.commit("plexus", message=u"x\n\nBuilt-with: Plexus 0.9\n")
        self.assertEqual(self.message().count("Built-with"), 1)

    def test_nothing_to_commit_is_said(self):
        code, _, err = self.commit()
        self.assertEqual(code, 1)
        self.assertIn("name the paths", err)


class Undeploy(Tmp):
    """Removal is held to deploy's standard: the user's lines survive, or nothing changes."""

    def deployed(self):
        write(os.path.join(self.dir, "CLAUDE.md"), u"# Мои правила\n\n- линтер перед коммитом\n")
        write(os.path.join(self.dir, ".gitignore"), u"node_modules/\n")
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        code, _, err = run([os.path.join(SCRIPTS, "deploy.py"), "."], self.dir,
                           stdin=SECTIONS % CLEAN_SPEC, home=self.home)
        self.assertEqual(code, 0, err)

    def undeploy(self, data):
        return run([os.path.join(SCRIPTS, "undeploy.py"), ".", "--data=" + data], self.dir, home=self.home)

    def test_archive_keeps_the_users_lines_and_is_one_commit(self):
        self.deployed()
        code, out, err = self.undeploy("archive")
        self.assertEqual(code, 0, err)
        self.assertEqual(read(os.path.join(self.dir, "CLAUDE.md")), u"# Мои правила\n\n- линтер перед коммитом\n")
        ignore = read(os.path.join(self.dir, ".gitignore"))
        self.assertNotIn("plexus:", ignore)
        self.assertIn("node_modules/", ignore)
        self.assertIn(".env", ignore)  # the secret patterns stay
        self.assertFalse(os.path.exists(os.path.join(self.dir, "plexus")))
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "docs", "plexus-archive", "state.md")))
        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.dir, stdout=subprocess.PIPE,
                                universal_newlines=True).stdout
        self.assertEqual(status, "")
        subprocess.run(["git", "revert", "--no-edit", "HEAD"], cwd=self.dir, stdout=subprocess.PIPE,
                       env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                                GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "plexus", "state.md")))

    def test_delete_and_a_charter_alone_takes_the_file(self):
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        self.assertEqual(run([os.path.join(SCRIPTS, "deploy.py"), "."], self.dir,
                             stdin=SECTIONS % CLEAN_SPEC, home=self.home)[0], 0)
        code, _, err = self.undeploy("delete")
        self.assertEqual(code, 0, err)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "CLAUDE.md")))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "plexus")))

    def test_an_unclean_tree_is_refused_and_nothing_changes(self):
        self.deployed()
        write(os.path.join(self.dir, "loose.txt"), u"x")
        before = read(os.path.join(self.dir, "CLAUDE.md"))
        code, _, err = self.undeploy("archive")
        self.assertEqual(code, 1)
        self.assertIn("not clean", err)
        self.assertEqual(read(os.path.join(self.dir, "CLAUDE.md")), before)

    def test_broken_markers_are_refused(self):
        self.deployed()
        path = os.path.join(self.dir, "CLAUDE.md")
        write(path, read(path).replace("<!-- plexus:end -->", ""))
        subprocess.run(["git", "commit", "-qam", "x"], cwd=self.dir,
                       env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                                GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))
        code, _, err = self.undeploy("keep")
        self.assertEqual(code, 1)
        self.assertIn("markers", err)
        self.assertTrue(os.path.isdir(os.path.join(self.dir, "plexus")))


class Charter(Tmp):
    """Update replaces the block by script: the commit rule and the user's rules survive."""

    def old_project(self):
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        self.assertEqual(run([os.path.join(SCRIPTS, "deploy.py"), "."], self.dir,
                             stdin=SECTIONS % CLEAN_SPEC, home=self.home)[0], 0)
        path = os.path.join(self.dir, "CLAUDE.md")
        text = read(path).replace("Managed by Plexus %s." % VERSION, "Managed by Plexus 0.9.0.")
        text = text.replace("- **Commits.**", u"- **Lint.** Run the linter before each commit.\n"
                            u"  > «линтер перед коммитом»\n- **Commits.**")
        write(path, u"# Мои правила\n\n" + text + u"\nпосле блока\n")
        return path

    def test_old_names_the_commit_rule_and_the_rules_the_template_lacks(self):
        self.old_project()
        code, out, _ = run([os.path.join(SCRIPTS, "charter.py"), "--old"], self.dir)
        self.assertEqual(code, 0)
        self.assertIn("Old charter: 0.9.0", out)
        self.assertIn("Commit without asking.", out)
        self.assertIn(u"- **Lint.** Run the linter before each commit.\n  > «линтер перед коммитом»", out)
        self.assertIn("not in the installed template: 1", out)

    def test_the_block_is_replaced_and_kept_rules_go_below_it(self):
        path = self.old_project()
        stdin = (u"=== commit rule\nCommit without asking.\n=== below\n"
                 u"- **Lint.** Run the linter before each commit.\n  > «линтер перед коммитом»\n")
        code, out, err = run([os.path.join(SCRIPTS, "charter.py"), "."], self.dir, stdin=stdin)
        self.assertEqual(code, 0, err)
        text = read(path)
        self.assertTrue(text.startswith(u"# Мои правила\n\n<!-- plexus:begin -->"))
        self.assertIn("Managed by Plexus %s." % VERSION, text)
        block, rest = text.split("<!-- plexus:end -->")
        self.assertNotIn("Lint", block)
        self.assertIn(u"«линтер перед коммитом»", rest)
        self.assertTrue(rest.endswith(u"после блока\n"))

    def test_broken_markers_are_refused_and_the_file_is_untouched(self):
        path = self.old_project()
        write(path, read(path).replace("<!-- plexus:end -->", ""))
        before = read(path)
        code, _, err = run([os.path.join(SCRIPTS, "charter.py"), "."], self.dir,
                           stdin=u"=== commit rule\nCommit without asking.\n")
        self.assertEqual(code, 1)
        self.assertEqual(read(path), before)


class Headers(Tmp):
    """A `#` inside a value is the value's: `C#` stays `C#`, not `C`."""

    def test_a_hash_inside_a_value_stays_and_a_comment_goes(self):
        os.makedirs(os.path.join(self.dir, "plexus", "tasks"))
        write(os.path.join(self.dir, "plexus", "tasks", "01-01-x.md"),
              u"---\nid: task-01-01\niteration: iteration-01\ntitle: C# parser handles issue #12\n"
              u"status: todo             # todo | done\nsize: S\nblocked_by: []\n---\n# x\n")
        _, out, _ = run([os.path.join(SCRIPTS, "tables.py"), "tasks"], self.dir)
        self.assertIn("C# parser handles issue #12", out)
        self.assertIn("todo", out)
        self.assertNotIn("todo | done", out)

    def test_the_brief_keeps_a_hash_inside_a_value(self):
        os.makedirs(os.path.join(self.dir, "plexus"))
        write(os.path.join(self.dir, "plexus", "state.md"),
              u"---\nstage: implement   # a comment\nnext: verify\niteration: iteration-01\n"
              u"task: task-01-01\n---\n\n# State\n")
        _, out, _ = run([os.path.join(SCRIPTS, "session_brief.py"), "SessionStart"], self.dir,
                        stdin="{}", home=self.home)
        brief = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[stage6]implement", brief)
        self.assertNotIn("a comment", brief)


class StateAndGit(Tmp):
    """Stages substitute where the work stopped through the one script they may run."""

    def test_state_and_git_are_printed(self):
        os.makedirs(os.path.join(self.dir, "plexus"))
        write(os.path.join(self.dir, "plexus", "state.md"), u"---\nstage: plan\n---\n# Где мы\n")
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        write(os.path.join(self.dir, "loose.txt"), u"x")
        code, out, _ = run([os.path.join(SCRIPTS, "tables.py"), "state", "git"], self.dir)
        self.assertEqual(code, 0)
        self.assertIn(u"# Где мы", out)
        self.assertIn("loose.txt", out)
        self.assertIn("Last commits: none yet", out)


class Secrets(Tmp):
    """The checklist's "no secrets" is a pattern search, not the model skimming a diff."""

    def commit(self, name, text):
        write(os.path.join(self.dir, name), text)
        subprocess.run(["git", "add", name], cwd=self.dir)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", name],
                       cwd=self.dir)

    def test_a_key_added_since_the_base_is_found_and_masked(self):
        subprocess.run(["git", "init", "-q"], cwd=self.dir)
        self.commit("a.py", u"x = 1\n")
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.dir, stdout=subprocess.PIPE,
                              universal_newlines=True).stdout.strip()
        key = "AKIA" + "ABCDEFGHIJKLMNOP"
        self.commit("b.py", u"ok = 2\naws = '%s'\npassword = os.environ['P']\n" % key)
        self.commit(".env", u"X=1\n")
        self.commit(".env.example", u"X=\n")
        code, out, _ = run([os.path.join(SCRIPTS, "secrets.py"), "diff", base], self.dir)
        self.assertEqual(code, 2)
        self.assertIn("b.py:2  AWS access key", out)
        self.assertNotIn(key, out)  # the check must not copy the secret into the conversation
        self.assertIn(".env  a file", out)
        self.assertNotIn(".env.example", out)
        self.assertNotIn("b.py:3", out)  # a value read from the environment is not a secret

    def test_a_clean_archive_passes_and_a_key_inside_one_does_not(self):
        import zipfile
        path = os.path.join(self.dir, "app.zip")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("app/main.js", "console.log(1)\n")
        self.assertEqual(run([os.path.join(SCRIPTS, "secrets.py"), "path", path], self.dir)[0], 0)
        with zipfile.ZipFile(path, "a") as z:
            z.writestr("app/key.pem", "-----BEGIN RSA PRIVATE KEY-----\n")
        code, out, _ = run([os.path.join(SCRIPTS, "secrets.py"), "path", path], self.dir)
        self.assertEqual(code, 2)
        self.assertIn("private key", out)


class SessionBrief(Tmp):
    def brief(self, charter_version):
        os.makedirs(os.path.join(self.dir, "plexus"), exist_ok=True)
        write(os.path.join(self.dir, "plexus", "state.md"), 
            u"---\nstage: init\nnext: discover\n---\n\n# State\n")
        write(os.path.join(self.dir, "CLAUDE.md"), 
            u"<!-- Managed by Plexus %s. Edits inside the markers are overwritten. -->\n" % charter_version)
        _, out, _ = run([os.path.join(SCRIPTS, "session_brief.py"), "SessionStart"], self.dir,
                        stdin="{}", home=self.home)
        return json.loads(out)["hookSpecificOutput"]["additionalContext"]

    def test_the_same_prerelease_version_is_not_reported_as_older(self):
        # the full stop after a prerelease version is not part of it
        self.assertNotIn("offer /plexus:update", self.brief(VERSION))

    def test_an_older_charter_is_reported(self):
        self.assertIn("offer /plexus:update", self.brief("0.0.1"))

    def test_the_product_version_comes_from_the_changelog(self):
        os.makedirs(os.path.join(self.dir, "plexus"))
        write(os.path.join(self.dir, "plexus", "changelog.md"),
              u"# Changelog\n\n## Unreleased\n\n## 0.2.0 — 2026-10-01\n\n## 0.1.0 — 2026-09-01\n")
        self.assertIn("Product version: 0.2.0", self.brief(VERSION))

    def test_a_fresh_session_is_told_not_to_offer_clearing(self):
        self.assertIn("do not offer to clear", self.brief(VERSION))


class GroundAndTemplates(Tmp):
    def test_an_empty_project_is_an_answer_not_a_failure(self):
        code, out, _ = run([os.path.join(SCRIPTS, "ground.py")], self.dir, home=self.home)
        self.assertEqual(code, 0)
        self.assertIn("absent", out)

    def test_the_code_reference_is_printed_only_where_there_is_code(self):
        _, out, _ = run([os.path.join(SCRIPTS, "templates.py"), "existing-code"], self.dir)
        self.assertIn("not needed", out)
        write(os.path.join(self.dir, "main.py"), u"print(1)\n")
        _, out, _ = run([os.path.join(SCRIPTS, "templates.py"), "existing-code"], self.dir)
        self.assertIn("=== init: a project with code", out)
        self.assertIn("=== plexus/architecture.md", out)  # the map is drawn from the code


class Manifest(unittest.TestCase):
    def test_every_skill_directory_is_registered_in_one_place(self):
        plugin = json.loads(read(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
        market = json.loads(read(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
        on_disk = sorted("./skills/" + d for d in os.listdir(os.path.join(ROOT, "skills")))
        self.assertEqual(sorted(plugin["skills"]), on_disk)
        self.assertNotIn("skills", market["plugins"][0])


if __name__ == "__main__":
    unittest.main()
