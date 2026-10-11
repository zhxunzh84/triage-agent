"""Tests for the Alert schema."""

import json

import pytest
from pydantic import ValidationError

from triage_agent.schemas import Alert


def valid_payload() -> dict:
    return {
        "id": "ALT-000001",
        "service": "payments-api",
        "metric": "http_5xx_rate",
        "threshold": 0.05,
        "observed": 0.31,
        "log_excerpt": "ERROR upstream timeout calling core-ledger",
    }


def parse(payload: dict) -> Alert:
    return Alert.model_validate_json(json.dumps(payload))


def test_valid_alert_parses() -> None:
    alert = parse(valid_payload())
    assert alert.id == "ALT-000001"
    assert alert.service == "payments-api"
    assert alert.metric == "http_5xx_rate"
    assert alert.threshold == 0.05
    assert alert.observed == 0.31
    assert alert.log_excerpt == "ERROR upstream timeout calling core-ledger"


def assert_single_error(payload: dict, field: str, error_type: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        parse(payload)
    errors = exc_info.value.errors()
    assert len(errors) == 1, errors
    assert errors[0]["loc"] == (field,)
    assert errors[0]["type"] == error_type


@pytest.mark.parametrize(
    "bad_id",
    [
        "12345",  # no prefix
        "XALT-000001",  # extra leading character
        "ALT-0000012",  # 7 digits
        "ALT-00001",  # 5 digits
    ],
)
def test_invalid_id_rejected(bad_id: str) -> None:
    assert_single_error(valid_payload() | {"id": bad_id}, "id", "string_pattern_mismatch")


@pytest.mark.parametrize(
    ("bad_service", "error_type"),
    [
        ("Payments-API", "string_pattern_mismatch"),  # uppercase letters
        ("payments api", "string_pattern_mismatch"),  # with space
        ("-service", "string_pattern_mismatch"),  # start with -
        ("a" * 65, "string_too_long"),  # too long
        ("", "string_pattern_mismatch"),  # empty string
    ],
)
def test_invalid_service_rejected(bad_service: str, error_type: str) -> None:
    assert_single_error(valid_payload() | {"service": bad_service}, "service", error_type)


@pytest.mark.parametrize(
    ("bad_metric", "error_type"),
    [
        ("", "string_too_short"),  # too short
        ("a" * 129, "string_too_long"),  # too long
    ],
)
def test_invalid_metric_rejected(bad_metric: str, error_type: str) -> None:
    assert_single_error(
        valid_payload() | {"metric": bad_metric},
        "metric",
        error_type,
    )


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


@pytest.mark.parametrize(
    ("bad_log_excerpt", "error_type"),
    [
        pytest.param("a" * 4001, "string_too_long", id="too-long-4001"),  # too long
        pytest.param(12345, "string_type", id="int-not-str"),  # not a string
    ],
)
def test_invalid_log_excerpt_rejected(bad_log_excerpt: object, error_type: str) -> None:
    assert_single_error(
        valid_payload() | {"log_excerpt": bad_log_excerpt}, "log_excerpt", error_type
    )


@pytest.mark.parametrize(
    "excerpt",
    [
        pytest.param("a" * 4000, id="max-length-4000"),  # max length
        pytest.param("", id="empty"),  # empty string
    ],
)
def test_log_excerpt_boundary_accepted(excerpt: str) -> None:
    alert = parse(valid_payload() | {"log_excerpt": excerpt})
    assert alert.log_excerpt == excerpt
