"""Tests for the TriageResult schema."""

import json

import pytest
from pydantic import ValidationError

from triage_agent.schemas import TriageResult

# ---------- helpers ----------


def valid_payload() -> dict:
    return {"severity": "P2", "runbook_id": "rb-scale-up"}


def parse(payload: dict) -> TriageResult:
    return TriageResult.model_validate_json(json.dumps(payload))


def assert_single_error(payload: dict, field: str, error_type: str) -> None:
    # Assert that a single validation error occurs for the given field and error type
    with pytest.raises(ValidationError) as exc_info:
        parse(payload)
    errors = exc_info.value.errors()
    assert len(errors) == 1, errors
    assert errors[0]["loc"] == (field,)
    assert errors[0]["type"] == error_type


# ---------- severity ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("P1", "P1", id="canonical"),
        pytest.param(" p2 ", "P2", id="lowercase-padded"),
    ],
)
def test_severity_normalized(raw: str, expected: str) -> None:
    payload = valid_payload() | {"severity": raw}
    assert parse(payload).severity == expected


@pytest.mark.parametrize(
    "bad_severity",
    [
        pytest.param("P5", id="out-of-range"),
        pytest.param("bad", id="word"),
        pytest.param("P 2", id="inner-space"),
        pytest.param(2, id="int"),
    ],
)
def test_invalid_severity_rejected(bad_severity: object) -> None:
    assert_single_error(valid_payload() | {"severity": bad_severity}, "severity", "literal_error")


# ---------- runbook_id ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("rb-rollback-deploy", "rb-rollback-deploy", id="canonical"),
        pytest.param(" rb-scale-up ", "rb-scale-up", id="padded"),
    ],
)
def test_runbook_id_normalized(raw: str, expected: str) -> None:
    payload = valid_payload() | {"runbook_id": raw}
    assert parse(payload).runbook_id == expected


@pytest.mark.parametrize(
    ("bad_runbook", "error_type"),
    [
        pytest.param("rb-delete-db", "value_error", id="not-in-allowlist"),
        pytest.param("RB-SCALE-UP", "value_error", id="wrong-case"),
        pytest.param(3, "string_type", id="int"),
    ],
)
def test_invalid_runbook_id_rejected(bad_runbook: object, error_type: str) -> None:
    assert_single_error(
        {
            "severity": "P2",
            "runbook_id": bad_runbook,
        },
        "runbook_id",
        error_type,
    )


def test_runbook_id_required() -> None:
    payload = valid_payload()
    del payload["runbook_id"]
    assert_single_error(payload, "runbook_id", "missing")
