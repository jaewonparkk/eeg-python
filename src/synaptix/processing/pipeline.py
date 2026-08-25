from dataclasses import dataclass

import numpy as np

from scipy.signal import (
    butter,
    filtfilt,
    iirnotch,
    sosfiltfilt,
)

from synaptix.core.recording import Recording
from synaptix.models.processing import ProcessingSettings


@dataclass(slots=True)
class ProcessingWindow:
    times: np.ndarray

    raw_data: np.ndarray
    processed_data: np.ndarray

    channels: list[str]


class EEGProcessingPipeline:
    """
    Non-destructive EEG preprocessing preview engine.

    The pipeline never modifies the original Recording.

    Only the currently requested time window plus a small
    padding region is loaded and processed. This preserves
    Synaptix's lazy-loading architecture.
    """

    def __init__(
        self,
        settings: ProcessingSettings,
    ):
        self.settings = settings

    # =========================================================
    # Public API
    # =========================================================

    def process_window(
        self,
        recording: Recording,
        start_seconds: float,
        duration_seconds: float,
        channels: list[str],
    ) -> ProcessingWindow:
        if not channels:
            return ProcessingWindow(
                times=np.array([]),
                raw_data=np.empty(
                    (
                        0,
                        0,
                    )
                ),
                processed_data=np.empty(
                    (
                        0,
                        0,
                    )
                ),
                channels=[],
            )

        self._validate_settings(
            recording
        )

        requested_start = max(
            0.0,
            start_seconds,
        )

        requested_end = min(
            recording.duration_seconds,
            requested_start
            + duration_seconds,
        )

        padding = (
            self.settings.preview_padding_seconds
        )

        context_start = max(
            0.0,
            requested_start
            - padding,
        )

        context_end = min(
            recording.duration_seconds,
            requested_end
            + padding,
        )

        context_duration = (
            context_end
            - context_start
        )

        # -----------------------------------------------------
        # Load only the required EEG window.
        # -----------------------------------------------------

        raw_context, context_times = (
            recording.get_window(
                start_seconds=context_start,
                duration_seconds=context_duration,
                channels=channels,
            )
        )

        if raw_context.size == 0:
            return ProcessingWindow(
                times=np.array([]),
                raw_data=np.empty(
                    (
                        len(channels),
                        0,
                    )
                ),
                processed_data=np.empty(
                    (
                        len(channels),
                        0,
                    )
                ),
                channels=channels,
            )

        # -----------------------------------------------------
        # Non-destructive copy.
        # -----------------------------------------------------

        processed_context = np.array(
            raw_context,
            dtype=np.float64,
            copy=True,
        )

        # -----------------------------------------------------
        # Processing
        # -----------------------------------------------------

        if self.settings.bandpass_enabled:
            processed_context = (
                self._apply_bandpass(
                    data=processed_context,
                    sampling_frequency=(
                        recording.sampling_frequency
                    ),
                )
            )

        if self.settings.notch_enabled:
            processed_context = (
                self._apply_notch(
                    data=processed_context,
                    sampling_frequency=(
                        recording.sampling_frequency
                    ),
                )
            )

        # -----------------------------------------------------
        # Remove padding after filtering.
        #
        # Padding reduces edge artifacts caused by filtering
        # directly at the visible window boundaries.
        # -----------------------------------------------------

        mask = (
            (context_times >= requested_start)
            & (
                context_times
                < requested_end
            )
        )

        times = context_times[
            mask
        ]

        raw_visible = raw_context[
            :,
            mask,
        ]

        processed_visible = (
            processed_context[
                :,
                mask,
            ]
        )

        return ProcessingWindow(
            times=times,
            raw_data=raw_visible,
            processed_data=processed_visible,
            channels=list(
                channels
            ),
        )

    # =========================================================
    # Band-pass
    # =========================================================

    def _apply_bandpass(
        self,
        data: np.ndarray,
        sampling_frequency: float,
    ) -> np.ndarray:
        low = (
            self.settings.highpass_hz
        )

        high = (
            self.settings.lowpass_hz
        )

        order = (
            self.settings.filter_order
        )

        # scipy butter with fs= accepts Hz directly.
        sos = butter(
            N=order,
            Wn=[
                low,
                high,
            ],
            btype="bandpass",
            fs=sampling_frequency,
            output="sos",
        )

        return sosfiltfilt(
            sos,
            data,
            axis=-1,
        )

    # =========================================================
    # Notch
    # =========================================================

    def _apply_notch(
        self,
        data: np.ndarray,
        sampling_frequency: float,
    ) -> np.ndarray:
        frequency = (
            self.settings.notch_hz
        )

        quality_factor = (
            self.settings.notch_q
        )

        b, a = iirnotch(
            w0=frequency,
            Q=quality_factor,
            fs=sampling_frequency,
        )

        return filtfilt(
            b,
            a,
            data,
            axis=-1,
        )

    # =========================================================
    # Validation
    # =========================================================

    def _validate_settings(
        self,
        recording: Recording,
    ):
        sampling_frequency = (
            recording.sampling_frequency
        )

        nyquist = (
            sampling_frequency / 2.0
        )

        if self.settings.bandpass_enabled:
            low = (
                self.settings.highpass_hz
            )

            high = (
                self.settings.lowpass_hz
            )

            if low <= 0:
                raise ValueError(
                    "High-pass frequency must "
                    "be greater than 0 Hz."
                )

            if high <= low:
                raise ValueError(
                    "Low-pass frequency must "
                    "be greater than the "
                    "high-pass frequency."
                )

            if high >= nyquist:
                raise ValueError(
                    (
                        "Low-pass frequency must be "
                        f"below Nyquist frequency "
                        f"({nyquist:.1f} Hz)."
                    )
                )

        if self.settings.notch_enabled:
            notch = (
                self.settings.notch_hz
            )

            if notch >= nyquist:
                raise ValueError(
                    (
                        "Notch frequency must be "
                        f"below Nyquist frequency "
                        f"({nyquist:.1f} Hz)."
                    )
                )