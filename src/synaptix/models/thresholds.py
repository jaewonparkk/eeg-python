from pydantic import BaseModel, Field


class DetectionThresholds(BaseModel):
    amplitude_uv: float = Field(
        default=150.0,
        gt=0,
        description="Maximum absolute EEG amplitude in microvolts",
    )

    gradient_uv: float = Field(
        default=75.0,
        gt=0,
        description="Maximum sample-to-sample voltage change in microvolts",
    )

    flatline_seconds: float = Field(
        default=2.0,
        gt=0,
        description="Minimum flatline duration",
    )

    flatline_tolerance_uv: float = Field(
        default=1.0,
        gt=0,
        description="Maximum voltage variation considered flat",
    )

    muscle_ratio: float = Field(
        default=0.35,
        ge=0,
        le=1,
        description="High-frequency power ratio threshold",
    )