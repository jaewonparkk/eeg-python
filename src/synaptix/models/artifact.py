from enum import Enum

from pydantic import BaseModel


class ArtifactType(str, Enum):
    HIGH_AMPLITUDE = "high_amplitude"
    RAPID_CHANGE = "rapid_change"
    FLATLINE = "flatline"
    MUSCLE = "muscle"
    EYE_BLINK = "eye_blink"
    UNKNOWN = "unknown"


class ArtifactCandidate(BaseModel):
    artifact_type: ArtifactType

    start_seconds: float
    end_seconds: float

    channels: list[str]

    confidence: float

    reason: str

    measured_value: float | None = None
    threshold_value: float | None = None

    accepted: bool | None = None