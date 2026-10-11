"""Alert schema: an incoming monitoring alert, validated strictly."""

from pydantic import BaseModel, ConfigDict, Field


class Alert(BaseModel):
    """A monitoring alert as received. Immutable once parsed."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    id: str = Field(pattern=r"^ALT-\d{6}$")
    service: str = Field(pattern=r"^[a-z][a-z0-9-]*$", max_length=64)
    metric: str = Field(min_length=1, max_length=128)
    threshold: float = Field(allow_inf_nan=False)
    observed: float = Field(allow_inf_nan=False)
    log_excerpt: str = Field(max_length=4000)
