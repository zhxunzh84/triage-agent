"""TriageResult schema: the LLM's triage output. Lenient on format, strict on rules."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    # lax on purpose: LLM output, normalize format
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    severity: Severity
    runbook_id: str
    summary: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("runbook_id")
    @classmethod
    def check_runbook_allowlist(cls, v: str) -> str:
        if v not in RUNBOOK_ALLOWLIST:
            raise ValueError(f"runbook_id {v!r} is not in the allowlist")
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def reject_bool_confidence(cls, v: object) -> object:
        if isinstance(v, bool):
            raise ValueError("confidence cannot be a boolean")
        return v
