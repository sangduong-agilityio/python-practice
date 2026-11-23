"""Tests for block-forbidden-command.py (run: python -m unittest discover -s .claude/hooks -p "test_*.py")."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "bfc", Path(__file__).with_name("block-forbidden-command.py")
)
bfc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bfc)


def make_repo(branch):
    tmp = tempfile.TemporaryDirectory()
    for args in (
        ["git", "init", "-q", "-b", branch],
        ["git", "config", "user.email", "t@example.com"],
        ["git", "config", "user.name", "T"],
        ["git", "commit", "-q", "--allow-empty", "-m", "init"],
    ):
        subprocess.run(args, cwd=tmp.name, check=True, capture_output=True)
    return tmp


class BlockForbiddenCommandTest(unittest.TestCase):
    def test_blocks_explicit_push_to_main(self):
        for cmd in (
            "git push origin main",
            "git push -u origin main",
            "git push origin HEAD:main",
            "git push origin feat/x:refs/heads/main",
            "git push origin master",
        ):
            self.assertIn("main directly", bfc.find_violation(cmd) or "", cmd)

    def test_allows_push_of_feature_and_epic_branches(self):
        for cmd in (
            "git push -u origin feat/task-comments/api",
            "git push origin epic/task-comments",
            "git push origin feat/maintenance/x",
        ):
            self.assertIsNone(bfc.find_violation(cmd), cmd)

    def test_bare_push_depends_on_current_branch(self):
        on_main = make_repo("main")
        on_feature = make_repo("feat/a/b")
        try:
            self.assertIsNotNone(bfc.find_violation("git push", on_main.name))
            self.assertIsNotNone(bfc.find_violation("git push origin HEAD", on_main.name))
            self.assertIsNone(bfc.find_violation("git push", on_feature.name))
            self.assertIsNone(bfc.find_violation("git push -u origin HEAD", on_feature.name))
        finally:
            on_main.cleanup()
            on_feature.cleanup()

    def test_blocks_no_verify(self):
        self.assertIsNotNone(bfc.find_violation('git commit --no-verify -m "x"'))
        self.assertIsNotNone(bfc.find_violation("git push --no-verify origin feat/a/b"))

    def test_commit_message_text_is_not_a_command(self):
        self.assertIsNone(bfc.find_violation('git commit -m "never push origin main"'))

    def test_existing_rules_still_apply(self):
        self.assertIsNotNone(bfc.find_violation("git push --force origin feat/a/b"))
        self.assertIsNotNone(bfc.find_violation("rm -rf build"))
        self.assertIsNone(bfc.find_violation("git status"))


if __name__ == "__main__":
    unittest.main()
