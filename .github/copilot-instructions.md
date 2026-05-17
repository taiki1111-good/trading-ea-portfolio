# Workspace Instructions for trading-ea

This repository uses repo-level workspace instructions to guide AI agents and collaborators during design, implementation, review, and experiment work.

## Primary workflow

- Start from `docs/00_how_to_continue.md` to understand repo intent and restart procedure.
- Use `AGENT_INDEX.md` and `REPO_MAP.md` for the high-level project map.
- Read core design docs before coding: `docs/02_requirements.md`, `docs/03_architecture.md`, `docs/04_module_spec.md`, `docs/05_variable_spec.md`, `docs/06_state_spec.md`, `docs/07_test_plan.md`, `docs/08_development_plan.md`.
- Confirm current priorities in `ops/CURRENT_TASKS.md`.
- Follow the agent workflow in `ops/AGENT_WORKFLOW.md` for AI/human role allocation.

## How to use AI assistance in this repo

- `5.4` is the design and architectural decision partner.
- `Copilot` / `Cursor` are used for structured code generation, scaffolding, and localized modifications.
- `Codex` is used for cross-file review, contract verification, and doc-code consistency checks.
- Human reviewers make final adoption decisions and update review logs.

## Repo structure and intent

- `docs/`: canonical design and requirements documentation.
- `ops/`: agent workflow, tasks, review queue, and decision logs.
- `src/`: implementation code.
- `tests/`: unit, integration, scenario, fixture, and experiment tests.
- `docs/experiments/`, `src/experiments/`, `tests/experiments/`: experimental patterns and prototype logic kept separate from main implementation.
- `portfolio/`: external-facing summaries and presentation drafts.

## Key rules for changes

- Do not implement code that contradicts requirements in `docs/02_requirements.md`.
- Keep module boundaries aligned with `docs/04_module_spec.md`.
- Use variable naming consistent with `docs/05_variable_spec.md`.
- Preserve state design from `docs/06_state_spec.md`.
- Ensure test coverage reflects `docs/07_test_plan.md`.
- Add or update documentation and logs for significant changes:
  - `ops/worklog/`
  - `ops/review/PENDING_REVIEW.md`
  - `ops/review/APPROVED_CHANGES.md`
  - `ops/DECISION_LOG.md`

## Experiments guidance

- New discretionary rules or hypotheses belong in `docs/experiments/`, `src/experiments/`, and `tests/experiments/`.
- Do not merge experiment-only logic directly into the main implementation without explicit review and adoption.

## Notes for AI agents

- Prefer linking to existing docs instead of duplicating content.
- If a prompt asks for implementation details, verify the relevant sections in `docs/04_module_spec.md`, `docs/05_variable_spec.md`, and `docs/06_state_spec.md` first.
- If build or environment commands are not yet defined in the repo, ask the user before adding new toolchain assumptions.
