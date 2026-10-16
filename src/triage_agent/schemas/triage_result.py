"""TriageResult schema: the LLM's triage output. Lenient on format, strict on rules."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Severity = Literal["P1", "P2", "P3", "P4"]


class TriageResult(BaseModel):
    model_config = ConfigDict(frozen=True)  # lax on purpose: LLM output, normalize format

    severity: Severity

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().upper()
        return v
