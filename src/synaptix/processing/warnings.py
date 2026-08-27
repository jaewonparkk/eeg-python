from synaptix.core.recording import (
    Recording,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
    PipelineStep,
    StepType,
)


class PipelineWarningEngine:
    @staticmethod
    def warnings_for_step(
        step: PipelineStep,
        pipeline: PipelineConfiguration,
        recording: Recording | None,
    ) -> list[str]:
        warnings: list[str] = []

        if recording is None:
            warnings.append(
                (
                    "Open an EEG recording "
                    "to validate this step "
                    "against recording metadata."
                )
            )

            return warnings

        sampling_frequency = (
            recording.sampling_frequency
        )

        nyquist = (
            sampling_frequency
            / 2.0
        )

        # =====================================================
        # Band-pass
        # =====================================================

        if (
            step.step_type
            == StepType.BANDPASS
        ):
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

            if highpass <= 0:
                warnings.append(
                    (
                        "High-pass frequency "
                        "must be greater than 0 Hz."
                    )
                )

            if lowpass <= highpass:
                warnings.append(
                    (
                        "Low-pass frequency "
                        "must be greater than "
                        "high-pass frequency."
                    )
                )

            if lowpass >= nyquist:
                warnings.append(
                    (
                        "Low-pass frequency must "
                        "remain below the Nyquist "
                        f"frequency of {nyquist:.1f} Hz."
                    )
                )

        # =====================================================
        # Notch
        # =====================================================

        if (
            step.step_type
            == StepType.NOTCH
        ):
            frequency = float(
                step.parameters.get(
                    "frequency_hz",
                    60.0,
                )
            )

            if frequency >= nyquist:
                warnings.append(
                    (
                        "Notch frequency must "
                        "remain below the Nyquist "
                        f"frequency of {nyquist:.1f} Hz."
                    )
                )

        # =====================================================
        # Average reference
        # =====================================================

        if (
            step.step_type
            == StepType.AVERAGE_REFERENCE
        ):
            manually_excluded = list(
                step.parameters.get(
                    "exclude_channels",
                    [],
                )
            )

            bad_channels = list(
                recording.bad_channels
            )

            unknown = [
                channel
                for channel
                in manually_excluded
                if channel
                not in recording.eeg_channels
            ]

            if unknown:
                warnings.append(
                    (
                        "Manual reference exclusions "
                        "were not found in the EEG: "
                        + ", ".join(
                            unknown
                        )
                    )
                )

            combined_exclusions = set(
                manually_excluded
            ) | set(
                bad_channels
            )

            eligible = [
                channel
                for channel
                in recording.eeg_channels
                if channel
                not in combined_exclusions
            ]

            if len(
                eligible
            ) < 2:
                warnings.append(
                    (
                        "Average reference has "
                        "fewer than two eligible "
                        "EEG channels."
                    )
                )

            if bad_channels:
                warnings.append(
                    (
                        "Marked bad channels will "
                        "be automatically excluded "
                        "from the average reference: "
                        + ", ".join(
                            bad_channels
                        )
                    )
                )

            else:
                warnings.append(
                    (
                        "No channels are currently "
                        "marked bad. Review Channel "
                        "Quality before relying on "
                        "an ordinary average reference."
                    )
                )

            step_index = (
                pipeline.steps.index(
                    step
                )
            )

            bandpass_indices = [
                index
                for index, candidate
                in enumerate(
                    pipeline.steps
                )
                if (
                    candidate.enabled
                    and candidate.step_type
                    == StepType.BANDPASS
                )
            ]

            if (
                bandpass_indices
                and step_index
                < bandpass_indices[
                    0
                ]
            ):
                warnings.append(
                    (
                        "Order note: Average "
                        "Reference currently runs "
                        "before Band-pass Filter. "
                        "Verify that this ordering "
                        "is intentional."
                    )
                )

        return warnings

    @classmethod
    def all_warnings(
        cls,
        pipeline: PipelineConfiguration,
        recording: Recording | None,
    ) -> list[str]:
        warnings: list[str] = []

        for step in pipeline.steps:
            if not step.enabled:
                continue

            warnings.extend(
                cls.warnings_for_step(
                    step=step,
                    pipeline=pipeline,
                    recording=recording,
                )
            )

        return warnings