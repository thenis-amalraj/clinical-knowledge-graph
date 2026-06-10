---
name: changelog
description: Generate a changelog entry for the current branch and append it to CHANGELOG.md.
disable-model-invocation: true
---
1. Run `git log main..HEAD --oneline` to get all commits on this branch.
2. Read the PR description if one exists (`gh pr view --json body`).
3. Categorize changes into: **Added**, **Changed**, **Fixed**, **Removed**.
4. Write user-facing summaries — describe the behavior change, not the implementation detail.
5. Append to `CHANGELOG.md` under a new `## [Unreleased] - <date>` section at the top of the file.
6. Do NOT modify any existing changelog entries.
