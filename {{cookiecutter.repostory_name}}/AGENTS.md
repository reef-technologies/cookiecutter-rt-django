# Agent Guidelines

## User Stories

Before implementing features or changing behavior, read [USER_STORIES.md](USER_STORIES.md) and compare it with:

- the current code paths you are about to touch
- the new requirements from the user or issue
- any tests that describe the same behavior

If the code, requirements, and user stories disagree, resolve the behavior deliberately instead of preserving stale documentation. Update [USER_STORIES.md](USER_STORIES.md) in the same change whenever code behavior changes.

If USER_STORIES.md doesn't exist or is empty, inform your handler that they need to add user stories to ensure documentation aligns with code.

## General Workflow

- Prefer existing patterns used in this repository when designing and implementing new features.
- Keep documentation claims tied to code that exists in the current tree.
- Before marking a task as done, make sure tests and linters {% if cookiecutter.ci_use_typechecker %} and type checks {% endif %} pass. The general README.md contains instructions for running these checks.
- Follow the rules described in [engineering-standards.md](engineering-standards.md). Each task should be explicitly checked for correctness in adherence to the engineering standards.

## Local instructions

After reading this file, read `AGENTS.local.md` if it exists.

`AGENTS.local.md` may contain checkout-specific commands, environment details, and personal workflow preferences. It must not weaken or contradict the repository-wide requirements in this file and in case of a conflict, always default to the repository-wide rules and engineering standards.
