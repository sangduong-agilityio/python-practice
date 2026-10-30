Perform a fast regression check and repository health audit:
1. Run `pytest tests/test_tasks.py -v` to ensure core task endpoints and filters pass.
2. Run `git status --short` to inspect modified and untracked files.
3. Summarize the status cleanly: state whether tests are green and list files requiring commit or cleanup.
