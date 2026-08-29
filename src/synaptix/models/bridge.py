from pydantic import BaseModel, Field


class BridgeDetectionSettings(BaseModel):
    enabled: bool = True

    lm_cutoff_uv2: float = Field(
        default=16.0,
        gt=0,
    )

    epoch_threshold: float = Field(
        default=0.5,
        gt=0,
        le=1,
    )

    low_frequency_hz: float = Field(
        default=0.5,
        gt=0,
    )

    high_frequency_hz: float = Field(
        default=30.0,
        gt=0,
    )

    epoch_duration_seconds: float = Field(
        default=2.0,
        gt=0,
    )


class BridgeCandidate(BaseModel):
    channel_a: str
    channel_b: str

    channel_index_a: int
    channel_index_b: int

    median_electrical_distance_uv2: float

    minimum_electrical_distance_uv2: float

    fraction_below_search_cutoff: float

    epoch_count: int

    reason: str

    # None = unreviewed
    # True = researcher confirmed bridge
    # False = researcher rejected bridge
    confirmed: bool | None = None