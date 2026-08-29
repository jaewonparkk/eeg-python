import mne
import numpy as np

from synaptix.core.recording import (
    Recording,
)
from synaptix.models.bridge import (
    BridgeCandidate,
    BridgeDetectionSettings,
)


class ElectrodeBridgeAnalyzer:
    """
    Detect electrode-bridge candidates using MNE's
    intrinsic Hjorth electrical-distance implementation.

    Detection results should be reviewed by a human
    before any correction is applied.
    """

    def __init__(
        self,
        settings: BridgeDetectionSettings,
    ):
        self.settings = settings

    def analyze_recording(
        self,
        recording: Recording,
    ) -> list[
        BridgeCandidate
    ]:
        if not self.settings.enabled:
            return []

        if (
            self.settings.high_frequency_hz
            <= self.settings.low_frequency_hz
        ):
            raise ValueError(
                (
                    "Bridge detection high-frequency "
                    "cutoff must be greater than "
                    "the low-frequency cutoff."
                )
            )

        nyquist = (
            recording.sampling_frequency
            / 2.0
        )

        if (
            self.settings.high_frequency_hz
            >= nyquist
        ):
            raise ValueError(
                (
                    "Bridge detection high-frequency "
                    "cutoff must remain below "
                    f"Nyquist ({nyquist:.1f} Hz)."
                )
            )

        # -----------------------------------------------------
        # Work on a COPY so detection never mutates the
        # original recording.
        #
        # Pick EEG only so returned bridge indices map directly
        # to eeg_raw.ch_names.
        # -----------------------------------------------------

        eeg_raw = (
            recording.copy_raw(
                load_data=True
            )
            .pick(
                "eeg"
            )
        )

        if len(
            eeg_raw.ch_names
        ) < 2:
            raise ValueError(
                (
                    "Bridge detection requires "
                    "at least two EEG channels."
                )
            )

        bridged_indices, ed_matrix = (
            mne.preprocessing
            .compute_bridged_electrodes(
                eeg_raw,
                lm_cutoff=(
                    self.settings
                    .lm_cutoff_uv2
                ),
                epoch_threshold=(
                    self.settings
                    .epoch_threshold
                ),
                l_freq=(
                    self.settings
                    .low_frequency_hz
                ),
                h_freq=(
                    self.settings
                    .high_frequency_hz
                ),
                epoch_duration=(
                    self.settings
                    .epoch_duration_seconds
                ),
                verbose=False,
            )
        )

        results: list[
            BridgeCandidate
        ] = []

        for (
            index_a,
            index_b,
        ) in bridged_indices:
            channel_a = (
                eeg_raw.ch_names[
                    index_a
                ]
            )

            channel_b = (
                eeg_raw.ch_names[
                    index_b
                ]
            )

            distances = np.asarray(
                ed_matrix[
                    :,
                    index_a,
                    index_b,
                ],
                dtype=float,
            )

            distances = distances[
                np.isfinite(
                    distances
                )
            ]

            if len(
                distances
            ) == 0:
                median_distance = 0.0
                minimum_distance = 0.0
                fraction_below = 0.0
                epoch_count = 0

            else:
                median_distance = float(
                    np.median(
                        distances
                    )
                )

                minimum_distance = float(
                    np.min(
                        distances
                    )
                )

                fraction_below = float(
                    np.mean(
                        distances
                        <= self.settings
                        .lm_cutoff_uv2
                    )
                )

                epoch_count = int(
                    len(
                        distances
                    )
                )

            reason = (
                f"{channel_a} and {channel_b} were "
                "flagged by MNE's intrinsic Hjorth "
                "electrical-distance bridge detector. "
                f"Median electrical distance was "
                f"{median_distance:.3f} µV² across "
                f"{epoch_count} epochs. "
                f"{fraction_below * 100:.1f}% of epochs "
                "fell below the configured local-minimum "
                f"search ceiling of "
                f"{self.settings.lm_cutoff_uv2:.1f} µV². "
                "The final bridge decision comes from "
                "the distribution-based electrical-distance "
                "algorithm, not from this percentage alone."
            )

            results.append(
                BridgeCandidate(
                    channel_a=channel_a,
                    channel_b=channel_b,
                    channel_index_a=(
                        index_a
                    ),
                    channel_index_b=(
                        index_b
                    ),
                    median_electrical_distance_uv2=(
                        median_distance
                    ),
                    minimum_electrical_distance_uv2=(
                        minimum_distance
                    ),
                    fraction_below_search_cutoff=(
                        fraction_below
                    ),
                    epoch_count=(
                        epoch_count
                    ),
                    reason=reason,
                )
            )

        return sorted(
            results,
            key=lambda candidate: (
                candidate
                .median_electrical_distance_uv2,
                candidate.channel_a,
                candidate.channel_b,
            ),
        )