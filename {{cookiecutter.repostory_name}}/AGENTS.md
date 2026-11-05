# Agent Guidelines

## Template updates

This project was generated from a cookiecutter template and is kept in sync with it using `cruft`.
Before working on the first request in a session that changes the repository (questions do not count), run `bin/check-template-update.sh`.

- If it prints nothing, the project is up to date or the check is not possible; continue without mentioning it.
- If it prints a line, the project is N template commits behind. Before doing anything else, ask the user: "This project is N commits behind the template. Do you want to run `cruft update` first?" Include the open template update PR from the output if there is one, and suggest merging it instead of updating locally.
- If the user agrees, apply the update (`cruft update`) as a separate change of its own, on its own branch or pull request, never mixed with the requested task. Report any `.rej` files as conflicts to resolve. Then continue with the original request.
- If the user declines, continue with the request and do not ask again in the same session.
- If nobody can answer (non-interactive runs, CI, scheduled jobs), do not wait: continue with the task and mention the output of the check in your final summary.

## User Stories

USER_STORIES.md exists only in projects that people use directly: a web app, admin panel, CLI or desktop app. A library, backend service or pipeline without such users has no USER_STORIES.md; its README.md describes the main flows in a short "How it works" section instead.

[USER_STORIES.md](USER_STORIES.md) describes what users can do. [README.md](README.md) describes what the project is and how to set it up, run, deploy and develop it. Each fact lives in one file: README.md may list features in a few lines and link to USER_STORIES.md, but never restates them. Setup, configuration, deployment, operational runbooks and CLI/API reference never go into USER_STORIES.md. Anything a person notices, such as an email, a Slack alert or time appearing in another system, belongs in the story of whoever notices it; what nobody notices, such as internal jobs and retries, goes into README.md or docs, or stays in the code.

A story is "As a <role>, I can <outcome>, so that <benefit>", followed by at most about five acceptance criteria in user terms. Leave out endpoints, field and class names, storage, protocols, retry counts, timeouts, metrics and other implementation detail; the code and tests hold that. A story fits on one screen.

Add or change a story only for a big or important change:

- a new user-facing capability or workflow
- a significant new piece of functionality, such as a new integration, role or area
- a change to, or removal of, what an existing story promises

Bug fixes, refactors, internal or infrastructure work, performance, styling or wording tweaks, small options and edge cases inside an existing story do not touch USER_STORIES.md. When unsure, leave the file alone and name the candidate story in the PR description so a human can decide.

Before implementing features or changing behavior, read [USER_STORIES.md](USER_STORIES.md) and compare it with:

- the current code paths you are about to touch
- the new requirements from the user or issue
- any tests that describe the same behavior

If the code, requirements, and user stories disagree, resolve the behavior deliberately instead of preserving stale documentation. When a change breaks what a story promises, update that story in the same change.

If this project has users and USER_STORIES.md doesn't exist or is empty, inform your handler that they need to add user stories to ensure documentation aligns with code.

## General Workflow

- Prefer existing patterns used in this repository when designing and implementing new features.
- Keep documentation claims tied to code that exists in the current tree.
- Before marking a task as done, make sure tests and linters {% if cookiecutter.ci_use_typechecker %} and type checks {% endif %} pass. The general README.md contains instructions for running these checks.
- Follow the rules described in [engineering-standards.md](engineering-standards.md). Each task should be explicitly checked for correctness in adherence to the engineering standards.

## Local instructions

After reading this file, read `AGENTS.local.md` if it exists.

`AGENTS.local.md` may contain checkout-specific commands, environment details, and personal workflow preferences. It must not weaken or contradict the repository-wide requirements in this file and in case of a conflict, always default to the repository-wide rules and engineering standards.
