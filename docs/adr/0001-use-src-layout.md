# ADR 0001: Use src layout for the application package

- **Status:** Accepted
- **Date:** 2026-10-09
- **Deciders:** Zhang Xun (author), tech lead (reviewer)
- **Ticket:** S1-01a

## Context

The design doc planned a flat layout, with application code in a top-level
`app/` package. When the project was initialised, `uv init` generated a
packaged project instead: a `src/triage_agent/` package plus a
`[build-system]` section, so uv installs the project into `.venv` in
editable mode.

We need to choose one layout before any application code is written,
because changing it later means rewriting every import path.

## Options considered

1. **Flat layout (`app/`)**: matches the original design doc. Requires a
   pytest `pythonpath = ["."]` workaround so tests can import the code.
2. **src layout (`src/triage_agent/`)**: the package is installed into the
   environment, so tests and tools import the installed package instead of
   whatever happens to be in the working directory.

## Decision

Use the **src layout** with the package name `triage_agent`.

## Consequences

**Positive**
- Tests run against the installed package, which catches packaging
  mistakes (e.g. a missing `__init__.py`) early instead of in production.
- No `sys.path` / `pythonpath` workarounds in configuration.
- Clear boundary between shippable code (`src/`) and dev-only tooling
  (`tests/`, `evals/`, `migrations/`).

**Negative / trade-offs**
- Import paths differ from the design doc
  (`app.audit` → `triage_agent.audit`).
- `uv run` rebuilds the editable install when project metadata changes,
  adding a small delay.

## Follow-ups

- [ ] Update the design doc and the Sprint 1 brief: `app/` → `src/triage_agent/`.
