from pydantic import (
    BaseModel,
    Field,
)


class ChannelQualityThresholds(BaseModel):
    """
    Heuristic thresholds used to surface channels
    that may require human review.

    These thresholds do not constitute a definitive
    clinical or scientific bad-channel diagnosis.
    """

    extreme_amplitude_uv: float = Field(
        default=150.0,
        gt=0,
    )

    extreme_fraction: float = Field(
        default=0.01,
        ge=0,
        le=1,
    )

    flat_delta_uv: float = Field(
        default=0.5,
        gt=0,
    )

    flat_fraction: float = Field(
        default=0.10,
        ge=0,
        le=1,
    )

    high_std_ratio: float = Field(
        default=4.0,
        gt=1,
    )

    low_std_ratio: float = Field(
        default=0.25,
        gt=0,
        lt=1,
    )

    min_median_correlation: float = Field(
        default=0.10,
        ge=-1,
        le=1,
    )


class ChannelQualityResult(BaseModel):
    channel: str

    standard_deviation_uv: float

    peak_to_peak_uv: float

    extreme_fraction: float

    flat_fraction: float

    median_correlation: float | None

    std_ratio: float

    flagged: bool

    reasons: list[str]

    severity: float = Field(
        ge=0,
        le=1,
    )