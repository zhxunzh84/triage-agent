## What
Adds `triage_agent.schemas.Alert`, the validated input model for incoming monitoring alerts.

## Why
Every downstream step (rules, LLM triage, audit log) relies on alerts being well-formed.
Bad input is rejected at the boundary instead of propagating.

## Design decisions
- **Strict mode** for Alert (machine-generated input): no silent coercion such as "0.31" → 0.31.
  The LLM output model (S1-02b) will be lax on format but strict on rules.
- **`allow_inf_nan=False`** on threshold/observed: NaN compares False to everything,
  so `observed > threshold` would silently never fire.
- **`AwareDatetime`** for received_at: naive timestamps are ambiguous (±8h for SGT vs UTC)
  and break the audit timeline.
- **`tuple[str, ...]` for recent_changes**: `frozen=True` is shallow; a list field
  could still be mutated via `.append()`. Found during exercises, fixed by using a tuple.
- **`extra="forbid"`**: unknown fields (e.g. an injected `"action"`) are rejected.

## MAS AIRG reference (design inspiration, not a compliance claim)
- 5.17 reproducibility/auditability: immutable model, timezone-aware timestamps
- Human oversight: no unapproved fields can enter the pipeline

## Tests
33 tests in `tests/test_schemas_alert.py`, covering each field's rejection paths
(asserting error `loc` + `type`), boundary pairs (4000/4001, 5/7 digits),
defaults, and model-level guarantees. Reverse-verified: removing each
constraint makes exactly the corresponding test fail.

## Known issue
Commits 988128a–6157f1c import pydantic before the dependency commit lands,
so they don't build in isolation. The branch tip is complete and green.
Lesson noted: dependency commits go first.

## Checklist
- [x] `make lint` green
- [x] `make test` green
- [x] Reverse verification done for allow_inf_nan, max_length, extra, frozen
