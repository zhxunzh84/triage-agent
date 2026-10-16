"""TriageResult schema: the LLM's triage output. Lenient on format, strict on rules."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Severity = Literal["P1", "P2", "P3", "P4"]
RUNBOOK_ALLOWLIST = frozenset(
    {
        "rb-rollback-deploy",
        "rb-scale-up",
        "rb-restart-pod",
        "rb-escalate-oncall",
    }
)


class TriageResult(BaseModel):
    """Triage decision proposed by the LLM. Validated before any action is considered."""

    model_config = ConfigDict(frozen=True)  # lax on purpose: LLM output, normalize format

    severity: Severity
    runbook_id: str

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("runbook_id", mode="before")
    @classmethod
    def normalize_runbook_id(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("runbook_id")
    @classmethod
    def check_runbook_allowlist(cls, v: str) -> str:
        if v not in RUNBOOK_ALLOWLIST:
            raise ValueError(f"runbook_id '{v!r}' is not in the allowlist")
        return v
