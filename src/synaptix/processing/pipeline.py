from dataclasses import (
    dataclass,
)

import numpy as np

from scipy.signal import (
    butter,
    filtfilt,
    iirnotch,
    sosfiltfilt,
)

from synaptix.core.recording import (
    Recording,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
    PipelineStep,
    StepType,
)


@dataclass(
    slots=True,
)
class ProcessingWindow:
    times: np.ndarray

    raw_data: np.ndarray

    processed_data: np.ndarray

    channels: list[str]


class EEGProcessingPipeline:
    """
    Non-destructive EEG preview engine.

    Steps execute in the exact user-configured order.
    The original Recording signal is never modified.
    """

    def __init__(
        self,
        configuration: PipelineConfiguration,
    ):
        self.configuration = (
            configuration
        )

    # =========================================================
    # Process window
    # =========================================================

    def process_window(
        self,
        recording: Recording,
        start_seconds: float,
        duration_seconds: float,
        channels: list[str],
    ) -> ProcessingWindow:
        if not channels:
            return self._empty_result(
                channels
            )

        requested_start = max(
            0.0,
            start_seconds,
        )

        requested_end = min(
            recording.duration_seconds,
            (
                requested_start
                + duration_seconds
            ),
        )

        padding = (
            self.configuration
            .preview_padding_seconds
        )

        context_start = max(
            0.0,
            (
                requested_start
                - padding
            ),
        )

        context_end = min(
            recording.duration_seconds,
            (
                requested_end
                + padding
            ),
        )

        context_duration = (
            context_end
            - context_start
        )

        # =====================================================
        # Reference requires all EEG channels
        # =====================================================

        average_reference_enabled = any(
            (
                step.enabled
                and step.step_type
                == StepType.AVERAGE_REFERENCE
            )
            for step
            in self.configuration.steps
        )

        if average_reference_enabled:
            processing_channels = list(
                dict.fromkeys(
                    recording.eeg_channels
                    + channels
                )
            )

        else:
            processing_channels = list(
                channels
            )

        raw_context, context_times = (
            recording.get_window(
                start_seconds=(
                    context_start
                ),
                duration_seconds=(
                    context_duration
                ),
                channels=(
                    processing_channels
                ),
            )
        )

        if raw_context.size == 0:
            return self._empty_result(
                channels
            )

        processed_context = (
            np.array(
                raw_context,
                dtype=np.float64,
                copy=True,
            )
        )

        # =====================================================
        # Execute pipeline in exact order
        # =====================================================

        for step in (
            self.configuration.steps
        ):
            if not step.enabled:
                continue

            processed_context = (
                self._execute_step(
                    step=step,
                    data=processed_context,
                    channel_names=(
                        processing_channels
                    ),
                    recording=recording,
                )
            )

        # =====================================================
        # Return visible channels only
        # =====================================================

        display_indices = [
            processing_channels.index(
                channel
            )
            for channel
            in channels
        ]

        visible_mask = (
            (
                context_times
                >= requested_start
            )
            & (
                context_times
                < requested_end
            )
        )

        raw_visible = (
            raw_context[
                display_indices,
                :
            ][
                :,
                visible_mask,
            ]
        )

        processed_visible = (
            processed_context[
                display_indices,
                :
            ][
                :,
                visible_mask,
            ]
        )

        times = context_times[
            visible_mask
        ]

        return ProcessingWindow(
            times=times,
            raw_data=raw_visible,
            processed_data=(
                processed_visible
            ),
            channels=list(
                channels
            ),
        )

    # =========================================================
    # Execute step
    # =========================================================

    def _execute_step(
        self,
        step: PipelineStep,
        data: np.ndarray,
        channel_names: list[str],
        recording: Recording,
    ) -> np.ndarray:
        if (
            step.step_type
            == StepType.BANDPASS
        ):
            return self._bandpass(
                data=data,
                step=step,
                sampling_frequency=(
                    recording
                    .sampling_frequency
                ),
            )

        if (
            step.step_type
            == StepType.NOTCH
        ):
            return self._notch(
                data=data,
                step=step,
                sampling_frequency=(
                    recording
                    .sampling_frequency
                ),
            )

        if (
            step.step_type
            == StepType.AVERAGE_REFERENCE
        ):
            return (
                self._average_reference(
                    data=data,
                    step=step,
                    channel_names=(
                        channel_names
                    ),
                    recording=(
                        recording
                    ),
                )
            )

        return data

    # =========================================================
    # Band-pass
    # =========================================================

    @staticmethod
    def _bandpass(
        data: np.ndarray,
        step: PipelineStep,
        sampling_frequency: float,
    ) -> np.ndarray:
        highpass = float(
            step.parameters.get(
                "highpass_hz",
                0.5,
            )
        )

        lowpass = float(
            step.parameters.get(
                "lowpass_hz",
                45.0,
            )
        )

        order = int(
            step.parameters.get(
                "order",
                4,
            )
        )

        nyquist = (
            sampling_frequency
            / 2.0
        )

        if highpass <= 0:
            raise ValueError(
                (
                    "High-pass must be "
                    "greater than 0 Hz."
                )
            )

        if lowpass <= highpass:
            raise ValueError(
                (
                    "Low-pass must be "
                    "greater than high-pass."
                )
            )

        if lowpass >= nyquist:
            raise ValueError(
                (
                    "Low-pass must remain "
                    "below Nyquist frequency "
                    f"({nyquist:.1f} Hz)."
                )
            )

        sos = butter(
            N=order,
            Wn=[
                highpass,
                lowpass,
            ],
            btype="bandpass",
            fs=(
                sampling_frequency
            ),
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

    @staticmethod
    def _notch(
        data: np.ndarray,
        step: PipelineStep,
        sampling_frequency: float,
    ) -> np.ndarray:
        frequency = float(
            step.parameters.get(
                "frequency_hz",
                60.0,
            )
        )

        quality_factor = float(
            step.parameters.get(
                "quality_factor",
                30.0,
            )
        )

        nyquist = (
            sampling_frequency
            / 2.0
        )

        if frequency >= nyquist:
            raise ValueError(
                (
                    "Notch frequency must "
                    "remain below Nyquist "
                    f"frequency ({nyquist:.1f} Hz)."
                )
            )

        b, a = iirnotch(
            w0=frequency,
            Q=quality_factor,
            fs=(
                sampling_frequency
            ),
        )

        return filtfilt(
            b,
            a,
            data,
            axis=-1,
        )

    # =========================================================
    # Average reference
    # =========================================================

    @staticmethod
    def _average_reference(
        data: np.ndarray,
        step: PipelineStep,
        channel_names: list[str],
        recording: Recording,
    ) -> np.ndarray:
        manually_excluded = set(
            step.parameters.get(
                "exclude_channels",
                [],
            )
        )

        bad_channels = set(
            recording.bad_channels
        )

        eeg_indices = [
            index
            for index, channel
            in enumerate(
                channel_names
            )
            if channel
            in recording.eeg_channels
        ]

        # -----------------------------------------------------
        # Channels used to CALCULATE reference
        # -----------------------------------------------------

        reference_indices = [
            index
            for index
            in eeg_indices
            if (
                channel_names[
                    index
                ]
                not in manually_excluded
                and channel_names[
                    index
                ]
                not in bad_channels
            )
        ]

        if len(
            reference_indices
        ) < 2:
            raise ValueError(
                (
                    "Average reference needs "
                    "at least two eligible "
                    "good EEG channels."
                )
            )

        reference_signal = (
            np.mean(
                data[
                    reference_indices,
                    :
                ],
                axis=0,
            )
        )

        output = np.array(
            data,
            copy=True,
        )

        # -----------------------------------------------------
        # Match MNE-style bad-channel behavior:
        # marked bad channels remain untouched.
        # -----------------------------------------------------

        target_indices = [
            index
            for index
            in eeg_indices
            if (
                channel_names[
                    index
                ]
                not in bad_channels
            )
        ]

        output[
            target_indices,
            :
        ] = (
            output[
                target_indices,
                :
            ]
            - reference_signal
        )

        return output

    # =========================================================
    # Empty
    # =========================================================

    @staticmethod
    def _empty_result(
        channels: list[str] | None = None,
    ) -> ProcessingWindow:
        if channels is None:
            channels = []

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