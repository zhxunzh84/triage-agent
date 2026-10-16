"""Tests for the TriageResult schema."""

import json

import pytest
from pydantic import ValidationError

from triage_agent.schemas import TriageResult

# ---------- helpers ----------


def valid_payload() -> dict:
    return {"severity": "P2"}


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
    payload = valid_payload()
    payload["severity"] = raw
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
    assert_single_error({"severity": bad_severity}, "severity", "literal_error")
