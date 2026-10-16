"""Tests for the TriageResult schema."""

import json

import pytest
from pydantic import ValidationError

from triage_agent.schemas import TriageResult

# ---------- helpers ----------


def valid_payload() -> dict:
    return {
        "severity": "P2",
        "runbook_id": "rb-scale-up",
        "summary": "A valid summary",
        "confidence": 0.9,
    }


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
    assert_single_error(valid_payload() | {"runbook_id": bad_runbook}, "runbook_id", error_type)


def test_runbook_id_required() -> None:
    payload = valid_payload()
    del payload["runbook_id"]
    assert_single_error(payload, "runbook_id", "missing")


# ---------- summary ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("  A valid summary  ", "A valid summary", id="stripped"),
        pytest.param("A" * 500, "A" * 500, id="max-length-500"),
    ],
)
def test_summary_accepted(raw: str, expected: str) -> None:
    payload = valid_payload() | {"summary": raw}
    assert parse(payload).summary == expected


@pytest.mark.parametrize(
    ("bad_summary", "error_type"),
    [
        pytest.param("A" * 501, "string_too_long", id="too-long-501"),
        pytest.param("   ", "string_too_short", id="whitespace-only"),
        pytest.param("", "string_too_short", id="empty"),
    ],
)
def test_invalid_summary_rejected(bad_summary: str, error_type: str) -> None:
    assert_single_error(valid_payload() | {"summary": bad_summary}, "summary", error_type)


# ---------- confidence ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param(0.0, 0.0, id="lower-bound-0"),
        pytest.param(1.0, 1.0, id="upper-bound-1"),
        pytest.param("0.5", 0.5, id="numeric-string"),
    ],
)
def test_confidence_accepted(raw: object, expected: float) -> None:
    payload = valid_payload() | {"confidence": raw}
    assert parse(payload).confidence == expected


@pytest.mark.parametrize(
    ("bad_confidence", "error_type"),
    [
        pytest.param(1.1, "less_than_equal", id="above-1"),
        pytest.param(-0.1, "greater_than_equal", id="below-0"),
        pytest.param("word", "float_parsing", id="word"),
        pytest.param(float("nan"), "finite_number", id="nan"),
        pytest.param(True, "value_error", id="bool"),
    ],
)
def test_invalid_confidence_rejected(bad_confidence: object, error_type: str) -> None:
    assert_single_error(valid_payload() | {"confidence": bad_confidence}, "confidence", error_type)
