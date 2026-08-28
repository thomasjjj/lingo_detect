# Repository Working Agreement

This file defines how coding agents should work in this repository.

The goal is to keep changes safe, reviewable, tested, documented, and easy for a human maintainer to understand. Prefer small, correct changes over broad rewrites.

## Instruction Priority

- Follow explicit user instructions first.
- Follow more specific repository or subdirectory instructions over this generic agreement.
- Follow existing project conventions over introducing new preferences.
- When instructions conflict, choose the safest interpretation and explain the conflict in the final response.
- Do not invent project conventions. Discover them from existing files, scripts, tests, docs, and CI configuration.

## Session Startup

Before making changes:

- Inspect the working tree with `git status`.
- Identify the project type, package manager, test framework, formatter, linter, and build system from existing files.
- Read relevant docs before editing:
  - `README.md`
  - `TODO.md` if present
  - files under `docs/` if relevant
  - CI workflows such as `.github/workflows/*` if present
  - package or build files such as `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `justfile`, `Taskfile.yml`, or similar
- Prefer existing scripts over raw tool commands.
- Do not run broad formatting, dependency upgrades, migrations, or code generation unless needed for the task.

## Protecting User Work

- Never overwrite, delete, move, reformat, or revert changes you did not make unless explicitly asked.
- Treat pre-existing uncommitted changes as user work.
- If user work conflicts with the requested change, stop and explain the conflict.
- Do not stage unrelated files.
- Do not amend, squash, rebase, reset, or force-push unless explicitly asked.
- Do not modify generated lockfiles, snapshots, schemas, or vendored files unless the task requires it and the change is understood.

## Repo Hygiene

- Keep the working tree tidy.
- Remove temporary files, scratch files, debug output, and local-only artifacts before finishing.
- If a generated artifact should not be committed, add an appropriate entry to `.gitignore`.
- Do not ignore files that are intentionally tracked by the project.
- Editor files, caches, build outputs, local databases, coverage reports, exported data, and one-off generated files should not be left as noisy untracked files.
- Keep changes small, focused, and easy to review.

## Project Commands

Use this section to record confirmed commands as the project matures.

- Test: `python -m unittest discover -s .\tests -v`
- Evaluate: `python .\tools\evaluate_detector.py`
- Generate corpora: `python .\tools\build_samples.py`
- Generate profiles: `python .\tools\build_language_profiles.py`
- Generate evaluation data: `python .\tools\build_test_samples.py`
- Build: `py -3.12 -m build`

Guidelines:

- Prefer project-provided commands over direct tool invocations.
- When you discover a reliable command, update this section.
- If commands are missing, infer cautiously from the project files and report what you used.
- If a command fails because dependencies or services are unavailable, report the exact command and failure reason.

## Task Tracking

- Track ongoing or multi-step work in `TODO.md`.
- Use Markdown checklists.
- When a task is finished, mark it complete but do not delete it.
- Add follow-up tasks when new work is discovered.
- Keep TODO entries concise and actionable.
- Do not create noisy TODO items for trivial one-step changes unless they represent real follow-up work.

## Completion And Commits

Agents must leave the repository in a clear state before ending a session.

- Commit completed, coherent changes before ending a session unless:
  - the user explicitly asks not to commit;
  - the active environment or session policy prevents commits;
  - tests or checks are failing and the change should not be committed;
  - unresolved questions make the change unsafe to commit;
  - the work is exploratory and not intended to be preserved.
- If completed changes are not committed, explain why in the final response.
- Before committing:
  - inspect `git status`;
  - review the diff;
  - stage only intended files;
  - run relevant tests or checks when practical;
  - ensure no secrets, local paths, credentials, tokens, private data, or unrelated artifacts are included.
- Commit messages should be short and descriptive.
- Use this style unless the project already uses another convention:

