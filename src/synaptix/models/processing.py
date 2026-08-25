from pydantic import BaseModel, Field


class ProcessingSettings(BaseModel):
    # =========================================================
    # Band-pass filtering
    # =========================================================

    bandpass_enabled: bool = True

    highpass_hz: float = Field(
        default=0.5,
        ge=0,
    )

    lowpass_hz: float = Field(
        default=45.0,
        gt=0,
    )

    filter_order: int = Field(
        default=4,
        ge=1,
        le=10,
    )

    # =========================================================
    # Notch filtering
    # =========================================================

    notch_enabled: bool = False

    notch_hz: float = Field(
        default=60.0,
        gt=0,
    )

    notch_q: float = Field(
        default=30.0,
        gt=0,
    )

    # =========================================================
    # Preview
    # =========================================================

    preview_padding_seconds: float = Field(
        default=2.0,
        ge=0,
    )