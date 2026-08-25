from pydantic import BaseModel, Field


class DetectionThresholds(BaseModel):
    # =========================================================
    # High amplitude
    # =========================================================

    amplitude_enabled: bool = True

    amplitude_uv: float = Field(
        default=150.0,
        gt=0,
        description=(
            "Absolute EEG amplitude above which a segment "
            "is flagged for human review."
        ),
    )

    # =========================================================
    # Rapid change
    # =========================================================

    rapid_change_enabled: bool = True

    rapid_change_uv: float = Field(
        default=75.0,
        gt=0,
        description=(
            "Maximum permitted sample-to-sample "
            "voltage change."
        ),
    )

    # =========================================================
    # Flatline
    # =========================================================

    flatline_enabled: bool = True

    flatline_seconds: float = Field(
        default=2.0,
        gt=0,
        description=(
            "Minimum duration of near-flat EEG activity."
        ),
    )

    flatline_tolerance_uv: float = Field(
        default=2.0,
        gt=0,
        description=(
            "Maximum peak-to-peak variation for a signal "
            "to be considered near-flat."
        ),
    )