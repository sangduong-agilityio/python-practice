"""Tests for new_worktree.py, run against a throwaway repository."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import new_worktree as nw  # noqa: E402


def run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


class NewWorktreeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        run("git", "init", "-q", "-b", "main", cwd=self.repo)
        run("git", "config", "user.email", "t@example.com", cwd=self.repo)
        run("git", "config", "user.name", "Test", cwd=self.repo)
        (self.repo / "README.md").write_text("x\n")
        run("git", "add", ".", cwd=self.repo)
        run("git", "commit", "-q", "-m", "init", cwd=self.repo)
        (self.repo / ".env").write_text("SECRET=1\n")

    def tearDown(self):
        for line in nw.git("worktree", "list", "--porcelain", cwd=self.repo).splitlines():
            if line.startswith("worktree ") and Path(line[9:]).resolve() != self.repo.resolve():
                nw.git("worktree", "remove", "--force", line[9:], cwd=self.repo)
        self.tmp.cleanup()

    def test_default_base_and_path(self):
        self.assertEqual(nw.default_base("epic/task-comments"), "origin/main")
        self.assertEqual(nw.default_base("feat/task-comments/api"), "epic/task-comments")
        self.assertEqual(
            nw.default_path(self.repo, "feat/task-comments/api").name,
            "task-api-feat-task-comments-api",
        )

    def test_rejects_bad_branch_names(self):
        for bad in ("task-comments", "feat/x", "Feat/a/b", "epic/Task", "wip/a/b"):
            with self.assertRaises(nw.SetupError, msg=bad):
                nw.create(self.repo, bad, "main", None, fetch=False)

    def test_creates_worktree_and_copies_env(self):
        path = nw.create(self.repo, "epic/task-comments", "main", None, fetch=False)
        self.assertTrue((path / "README.md").is_file())
        self.assertEqual((path / ".env").read_text(), "SECRET=1\n")
        self.assertEqual(nw.git("branch", "--show-current", cwd=path), "epic/task-comments")

    def test_refuses_existing_path_and_branch(self):
        path = nw.create(self.repo, "epic/a", "main", None, fetch=False)
        with self.assertRaises(nw.SetupError):
            nw.create(self.repo, "epic/b", "main", path, fetch=False)
        with self.assertRaises(nw.SetupError):
            nw.create(self.repo, "epic/a", "main", self.root / "other", fetch=False)

    def test_prompt_mentions_plan_and_other_worktrees(self):
        epic = nw.plan_prompt("epic/task-comments", "origin/main", ["D:/x"])
        self.assertIn("docs/epics/task-comments.md", epic)
        self.assertIn("Stop after the plan", epic)
        self.assertIn("D:/x", epic)
        sub = nw.plan_prompt("feat/task-comments/api", "epic/task-comments", [])
        self.assertIn("docs/test-reports/task-comments.md", sub)


if __name__ == "__main__":
    unittest.main()
