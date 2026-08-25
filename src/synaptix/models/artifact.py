from enum import Enum

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    HIGH_AMPLITUDE = "high_amplitude"
    RAPID_CHANGE = "rapid_change"
    FLATLINE = "flatline"

    # These will be implemented later using ICA/component analysis.
    MUSCLE = "muscle"
    EYE = "eye"

    UNKNOWN = "unknown"


class ArtifactCandidate(BaseModel):
    artifact_type: ArtifactType

    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)

    channels: list[str]

    confidence: float = Field(
        ge=0,
        le=1,
    )

    reason: str

    measured_value: float | None = None
    threshold_value: float | None = None

    metric_name: str | None = None
    unit: str | None = None

    # None  = not reviewed
    # True  = accepted by reviewer
    # False = rejected by reviewer
    accepted: bool | None = None