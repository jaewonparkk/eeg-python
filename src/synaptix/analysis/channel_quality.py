from collections.abc import (
    Callable,
)

import numpy as np

from synaptix.core.recording import (
    Recording,
)
from synaptix.models.channel_quality import (
    ChannelQualityResult,
    ChannelQualityThresholds,
)


class ChannelQualityAnalyzer:
    """
    Chunked channel-quality analyzer.

    This module surfaces suspicious EEG channels
    for human review. It does not automatically
    declare channels scientifically invalid.
    """

    def __init__(
        self,
        thresholds: ChannelQualityThresholds,
    ):
        self.thresholds = (
            thresholds
        )

    # =========================================================
    # Analyze recording
    # =========================================================

    def analyze_recording(
        self,
        recording: Recording,
        chunk_seconds: float = 30.0,
        progress_callback: Callable[
            [int],
            None,
        ]
        | None = None,
    ) -> list[ChannelQualityResult]:
        channels = (
            recording.eeg_channels
        )

        if not channels:
            return []

        channel_count = len(
            channels
        )

        # =====================================================
        # Running statistics
        # =====================================================

        sample_count = 0

        difference_count = 0

        sums = np.zeros(
            channel_count,
            dtype=np.float64,
        )

        square_sums = np.zeros(
            channel_count,
            dtype=np.float64,
        )

        minimums = np.full(
            channel_count,
            np.inf,
            dtype=np.float64,
        )

        maximums = np.full(
            channel_count,
            -np.inf,
            dtype=np.float64,
        )

        extreme_counts = np.zeros(
            channel_count,
            dtype=np.int64,
        )

        flat_counts = np.zeros(
            channel_count,
            dtype=np.int64,
        )

        correlation_sums = np.zeros(
            channel_count,
            dtype=np.float64,
        )

        correlation_weights = np.zeros(
            channel_count,
            dtype=np.float64,
        )

        # =====================================================
        # Chunked scan
        # =====================================================

        total_duration = (
            recording.duration_seconds
        )

        current_start = 0.0

        while (
            current_start
            < total_duration
        ):
            duration = min(
                chunk_seconds,
                (
                    total_duration
                    - current_start
                ),
            )

            data, _ = (
                recording.get_window(
                    start_seconds=(
                        current_start
                    ),
                    duration_seconds=(
                        duration
                    ),
                    channels=channels,
                )
            )

            if data.size:
                data_uv = (
                    data
                    * 1_000_000
                )

                chunk_samples = (
                    data_uv.shape[1]
                )

                sample_count += (
                    chunk_samples
                )

                sums += np.sum(
                    data_uv,
                    axis=1,
                )

                square_sums += np.sum(
                    np.square(
                        data_uv
                    ),
                    axis=1,
                )

                minimums = np.minimum(
                    minimums,
                    np.min(
                        data_uv,
                        axis=1,
                    ),
                )

                maximums = np.maximum(
                    maximums,
                    np.max(
                        data_uv,
                        axis=1,
                    ),
                )

                # ---------------------------------------------
                # Extreme amplitude
                # ---------------------------------------------

                extreme_counts += np.sum(
                    (
                        np.abs(
                            data_uv
                        )
                        >= self.thresholds
                        .extreme_amplitude_uv
                    ),
                    axis=1,
                )

                # ---------------------------------------------
                # Near-flat sample-to-sample change
                # ---------------------------------------------

                if chunk_samples >= 2:
                    differences = np.abs(
                        np.diff(
                            data_uv,
                            axis=1,
                        )
                    )

                    difference_count += (
                        differences.shape[1]
                    )

                    flat_counts += np.sum(
                        (
                            differences
                            <= self.thresholds
                            .flat_delta_uv
                        ),
                        axis=1,
                    )

                # ---------------------------------------------
                # Correlation to robust cross-channel median
                # ---------------------------------------------

                median_signal = (
                    np.median(
                        data_uv,
                        axis=0,
                    )
                )

                median_std = float(
                    np.std(
                        median_signal
                    )
                )

                if median_std > 1e-12:
                    for index in range(
                        channel_count
                    ):
                        signal = (
                            data_uv[
                                index
                            ]
                        )

                        signal_std = float(
                            np.std(
                                signal
                            )
                        )

                        if (
                            signal_std
                            <= 1e-12
                        ):
                            continue

                        correlation = float(
                            np.corrcoef(
                                signal,
                                median_signal,
                            )[
                                0,
                                1,
                            ]
                        )

                        if np.isfinite(
                            correlation
                        ):
                            correlation_sums[
                                index
                            ] += (
                                correlation
                                * chunk_samples
                            )

                            correlation_weights[
                                index
                            ] += (
                                chunk_samples
                            )

            current_start += (
                duration
            )

            if (
                progress_callback
                is not None
            ):
                progress = int(
                    min(
                        100,
                        (
                            current_start
                            / total_duration
                        )
                        * 100,
                    )
                )

                progress_callback(
                    progress
                )

        # =====================================================
        # Final metrics
        # =====================================================

        if sample_count == 0:
            return []

        means = (
            sums
            / sample_count
        )

        variances = (
            square_sums
            / sample_count
            - np.square(
                means
            )
        )

        variances = np.maximum(
            variances,
            0.0,
        )

        standard_deviations = (
            np.sqrt(
                variances
            )
        )

        peak_to_peak = (
            maximums
            - minimums
        )

        extreme_fractions = (
            extreme_counts
            / sample_count
        )

        if difference_count > 0:
            flat_fractions = (
                flat_counts
                / difference_count
            )

        else:
            flat_fractions = (
                np.zeros(
                    channel_count
                )
            )

        valid_stds = (
            standard_deviations[
                standard_deviations
                > 1e-12
            ]
        )

        if len(
            valid_stds
        ):
            median_channel_std = float(
                np.median(
                    valid_stds
                )
            )

        else:
            median_channel_std = (
                1e-12
            )

        results: list[
            ChannelQualityResult
        ] = []

        for index, channel in enumerate(
            channels
        ):
            std_uv = float(
                standard_deviations[
                    index
                ]
            )

            std_ratio = (
                std_uv
                / median_channel_std
            )

            if (
                correlation_weights[
                    index
                ]
                > 0
            ):
                correlation = float(
                    correlation_sums[
                        index
                    ]
                    / correlation_weights[
                        index
                    ]
                )

            else:
                correlation = None

            reasons: list[str] = []

            # ---------------------------------------------
            # High variance / noisy channel
            # ---------------------------------------------

            if (
                std_ratio
                >= self.thresholds
                .high_std_ratio
            ):
                reasons.append(
                    (
                        "Signal variability is "
                        f"{std_ratio:.2f}× the "
                        "median EEG channel."
                    )
                )

            # ---------------------------------------------
            # Very low variance
            # ---------------------------------------------

            if (
                std_ratio
                <= self.thresholds
                .low_std_ratio
            ):
                reasons.append(
                    (
                        "Signal variability is only "
                        f"{std_ratio:.2f}× the "
                        "median EEG channel."
                    )
                )

            # ---------------------------------------------
            # Extreme amplitude
            # ---------------------------------------------

            extreme_fraction = float(
                extreme_fractions[
                    index
                ]
            )

            if (
                extreme_fraction
                >= self.thresholds
                .extreme_fraction
            ):
                reasons.append(
                    (
                        f"{extreme_fraction * 100:.2f}% "
                        "of samples exceed the "
                        f"{self.thresholds.extreme_amplitude_uv:.1f} "
                        "µV review threshold."
                    )
                )

            # ---------------------------------------------
            # Flat / near-flat
            # ---------------------------------------------

            flat_fraction = float(
                flat_fractions[
                    index
                ]
            )

            if (
                flat_fraction
                >= self.thresholds
                .flat_fraction
            ):
                reasons.append(
                    (
                        f"{flat_fraction * 100:.2f}% "
                        "of sample transitions change by "
                        f"≤ {self.thresholds.flat_delta_uv:.2f} µV."
                    )
                )

            # ---------------------------------------------
            # Low correlation to robust median
            # ---------------------------------------------

            if (
                correlation is not None
                and correlation
                <= self.thresholds
                .min_median_correlation
            ):
                reasons.append(
                    (
                        "Correlation to the robust "
                        "cross-channel median is low "
                        f"({correlation:.2f})."
                    )
                )

            severity = min(
                1.0,
                (
                    len(
                        reasons
                    )
                    / 3.0
                ),
            )

            results.append(
                ChannelQualityResult(
                    channel=channel,
                    standard_deviation_uv=(
                        std_uv
                    ),
                    peak_to_peak_uv=float(
                        peak_to_peak[
                            index
                        ]
                    ),
                    extreme_fraction=(
                        extreme_fraction
                    ),
                    flat_fraction=(
                        flat_fraction
                    ),
                    median_correlation=(
                        correlation
                    ),
                    std_ratio=float(
                        std_ratio
                    ),
                    flagged=bool(
                        reasons
                    ),
                    reasons=reasons,
                    severity=severity,
                )
            )

        return sorted(
            results,
            key=lambda result: (
                not result.flagged,
                -result.severity,
                result.channel,
            ),
        )