"""Smoke test for the triage-agent, ensuring it initializes correctly."""

import importlib
import sys

import pytest

SUBPACKAGES = ["schemas", "rules", "audit", "db", "api"]


def test_python_version() -> None:
    assert sys.version_info >= (3, 12), (
        f"Python 3.12 or higher is required, "
        f"found {sys.version_info.major}.{sys.version_info.minor}"
    )


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_importable(name: str) -> None:
    module = importlib.import_module(f"triage_agent.{name}")
    assert module.__file__ is not None, f"{name} is a namespace package; missing __init__.py?"
