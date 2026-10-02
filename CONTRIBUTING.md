# Contributing to ShareCircle

Thanks for helping improve ShareCircle.

## Workflow

1. Fork the repository.
2. Create a focused branch, for example `feature/improved-match-card`.
3. Install dependencies with `pip install -r requirements.txt`.
4. Make the smallest clear change that solves the issue.
5. Run `python -m pytest` before opening the pull request.
6. Include screenshots or request/response examples for UI/API changes.
7. Open a pull request using the repository checklist and explain what changed.

## Code style

Keep the project framework-light. Use parameterized SQL, small functions, existing Flask patterns, and browser-native APIs. Avoid adding dependencies unless they are essential and compatible with the no-build-tool architecture.

## Commit guidance

Use descriptive imperative commits, such as `Add unread message badge` or `Test rating uniqueness`.

## Reporting issues

Use the bug or feature templates in `.github/ISSUE_TEMPLATE/` so reports include enough context to reproduce the behavior.
