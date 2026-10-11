"""Tests for the Alert schema."""

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from triage_agent.schemas import Alert

# ---------- helpers ----------


def valid_payload() -> dict:
    return {
        "id": "ALT-000001",
        "service": "payments-api",
        "metric": "http_5xx_rate",
        "threshold": 0.05,
        "observed": 0.31,
        "log_excerpt": "ERROR upstream timeout calling core-ledger",
        "received_at": "2026-10-11T04:00:00Z",
    }


def parse(payload: dict) -> Alert:
    return Alert.model_validate_json(json.dumps(payload))


def assert_single_error(
    payload: dict, field: str, error_type: str, *, index: int | None = None
) -> None:
    expected_loc = (field,) if index is None else (field, index)
    with pytest.raises(ValidationError) as exc_info:
        parse(payload)
    errors = exc_info.value.errors()
    assert len(errors) == 1, errors
    assert errors[0]["loc"] == expected_loc
    assert errors[0]["type"] == error_type


# ---------- happy path ----------


def test_valid_alert_parses() -> None:
    alert = parse(valid_payload())
    assert alert.id == "ALT-000001"
    assert alert.service == "payments-api"
    assert alert.metric == "http_5xx_rate"
    assert alert.threshold == 0.05
    assert alert.observed == 0.31
    assert alert.log_excerpt == "ERROR upstream timeout calling core-ledger"
    assert alert.received_at == datetime(2026, 10, 11, 4, 0, tzinfo=UTC)


# ---------- id / service / metric ----------


@pytest.mark.parametrize(
    "bad_id",
    [
        pytest.param("12345", id="no-prefix"),
        pytest.param("XALT-000001", id="extra-leading-char"),
        pytest.param("ALT-0000012", id="7-digits"),
        pytest.param("ALT-00001", id="5-digits"),
    ],
)
def test_invalid_id_rejected(bad_id: str) -> None:
    assert_single_error(valid_payload() | {"id": bad_id}, "id", "string_pattern_mismatch")


@pytest.mark.parametrize(
    ("bad_service", "error_type"),
    [
        pytest.param("Payments-API", "string_pattern_mismatch", id="uppercase"),
        pytest.param("payments api", "string_pattern_mismatch", id="space"),
        pytest.param("-service", "string_pattern_mismatch", id="leading-dash"),
        pytest.param("a" * 65, "string_too_long", id="too-long-65"),
        pytest.param("", "string_pattern_mismatch", id="empty"),
    ],
)
def test_invalid_service_rejected(bad_service: str, error_type: str) -> None:
    assert_single_error(valid_payload() | {"service": bad_service}, "service", error_type)


@pytest.mark.parametrize(
    ("bad_metric", "error_type"),
    [
        pytest.param("", "string_too_short", id="empty"),
        pytest.param("a" * 129, "string_too_long", id="too-long-129"),
    ],
)
def test_invalid_metric_rejected(bad_metric: str, error_type: str) -> None:
    assert_single_error(valid_payload() | {"metric": bad_metric}, "metric", error_type)


# ---------- threshold / observed ----------


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        pytest.param("threshold", float("inf"), "finite_number", id="threshold-inf"),
        pytest.param("threshold", float("-inf"), "finite_number", id="threshold-neg-inf"),
        pytest.param("observed", float("nan"), "finite_number", id="observed-nan"),
        pytest.param("observed", "0.31", "float_type", id="observed-str"),
    ],
)
def test_invalid_number_rejected(field: str, value: object, error_type: str) -> None:
    assert_single_error(valid_payload() | {field: value}, field, error_type)


def test_int_accepted_as_float() -> None:
    alert = parse(valid_payload() | {"observed": 1})
    assert alert.observed == 1.0
    assert isinstance(alert.observed, float)


# ---------- log_excerpt ----------


@pytest.mark.parametrize(
    ("bad_log_excerpt", "error_type"),
    [
        pytest.param("a" * 4001, "string_too_long", id="too-long-4001"),
        pytest.param(12345, "string_type", id="int-not-str"),
    ],
)
def test_invalid_log_excerpt_rejected(bad_log_excerpt: object, error_type: str) -> None:
    assert_single_error(
        valid_payload() | {"log_excerpt": bad_log_excerpt}, "log_excerpt", error_type
    )


@pytest.mark.parametrize(
    "excerpt",
    [
        pytest.param("a" * 4000, id="max-length-4000"),
        pytest.param("", id="empty"),
    ],
)
def test_log_excerpt_boundary_accepted(excerpt: str) -> None:
    alert = parse(valid_payload() | {"log_excerpt": excerpt})
    assert alert.log_excerpt == excerpt


# ---------- recent_changes ----------


def test_recent_changes_item_must_be_str() -> None:
    assert_single_error(
        valid_payload() | {"recent_changes": ["ok", 123]},
        "recent_changes",
        "string_type",
        index=1,
    )


def test_recent_changes_defaults_to_empty() -> None:
    alert = parse(valid_payload())
    assert alert.recent_changes == ()


def test_recent_changes_parsed_as_tuple() -> None:
    alert = parse(valid_payload() | {"recent_changes": ["deploy v2.3.1", "config change"]})
    assert alert.recent_changes == ("deploy v2.3.1", "config change")
    assert isinstance(alert.recent_changes, tuple)


def test_recent_changes_immutable() -> None:
    alert = parse(valid_payload() | {"recent_changes": ["deploy v2.3.1"]})
    with pytest.raises(AttributeError):
        alert.recent_changes.append("x")  # type: ignore[attr-defined]


# ---------- received_at ----------


@pytest.mark.parametrize(
    ("bad_received_at", "error_type"),
    [
        pytest.param("2026-10-11T04:00:00", "timezone_aware", id="naive-no-tz"),
        pytest.param("not-a-date", "datetime_parsing", id="garbage"),
        pytest.param("2026-10-11", "datetime_parsing", id="date-only"),
        pytest.param(1760155200, "datetime_type", id="unix-timestamp"),
    ],
)
def test_invalid_received_at_rejected(bad_received_at: object, error_type: str) -> None:
    assert_single_error(
        valid_payload() | {"received_at": bad_received_at}, "received_at", error_type
    )


def test_received_at_required() -> None:
    payload = valid_payload()
    del payload["received_at"]
    assert_single_error(payload, "received_at", "missing")


def test_received_at_same_instant_across_timezones() -> None:
    utc = parse(valid_payload() | {"received_at": "2026-10-11T04:00:00Z"})
    sgt = parse(valid_payload() | {"received_at": "2026-10-11T12:00:00+08:00"})
    assert utc.received_at == sgt.received_at
    assert sgt.received_at.tzinfo is not None


# ---------- model-level guarantees ----------


def test_unknown_field_rejected() -> None:
    assert_single_error(valid_payload() | {"action": "restart"}, "action", "extra_forbidden")


def test_alert_is_frozen() -> None:
    alert = parse(valid_payload())
    with pytest.raises(ValidationError) as exc_info:
        alert.service = "other-service"  # type: ignore[misc]
    assert exc_info.value.errors()[0]["type"] == "frozen_instance"
