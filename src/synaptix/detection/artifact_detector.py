from collections.abc import Callable

import numpy as np

from synaptix.core.recording import Recording
from synaptix.models.artifact import (
    ArtifactCandidate,
    ArtifactType,
)
from synaptix.models.thresholds import (
    DetectionThresholds,
)


class ArtifactDetector:
    """
    Threshold-guided signal-quality candidate detector.

    IMPORTANT:
    These detections are not definitive artifact diagnoses.

    They identify suspicious EEG segments that should be
    reviewed by a human before preprocessing decisions
    are accepted.
    """

    def __init__(
        self,
        thresholds: DetectionThresholds,
    ):
        self.thresholds = thresholds

    # =========================================================
    # Full recording scan
    # =========================================================

    def detect_recording(
        self,
        recording: Recording,
        chunk_seconds: float = 30.0,
        progress_callback: Callable[[int], None] | None = None,
    ) -> list[ArtifactCandidate]:
        """
        Scan the entire recording in chunks.

        This avoids loading the full EEG into memory and
        allows Synaptix to scale to long recordings.
        """

        total_duration = recording.duration_seconds

        if total_duration <= 0:
            return []

        candidates: list[ArtifactCandidate] = []

        current_start = 0.0

        while current_start < total_duration:
            duration = min(
                chunk_seconds,
                total_duration - current_start,
            )

            chunk_candidates = self.detect_window(
                recording=recording,
                start_seconds=current_start,
                duration_seconds=duration,
            )

            candidates.extend(
                chunk_candidates
            )

            current_start += duration

            if progress_callback is not None:
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

        candidates = self._merge_candidates(
            candidates=candidates,
            merge_gap_seconds=0.25,
        )

        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.start_seconds,
                (
                    candidate.channels[0]
                    if candidate.channels
                    else ""
                ),
            ),
        )

    # =========================================================
    # Window scan
    # =========================================================

    def detect_window(
        self,
        recording: Recording,
        start_seconds: float,
        duration_seconds: float,
    ) -> list[ArtifactCandidate]:
        candidates: list[ArtifactCandidate] = []

        if self.thresholds.amplitude_enabled:
            candidates.extend(
                self.detect_high_amplitude(
                    recording=recording,
                    start_seconds=start_seconds,
                    duration_seconds=duration_seconds,
                )
            )

        if self.thresholds.rapid_change_enabled:
            candidates.extend(
                self.detect_rapid_changes(
                    recording=recording,
                    start_seconds=start_seconds,
                    duration_seconds=duration_seconds,
                )
            )

        if self.thresholds.flatline_enabled:
            candidates.extend(
                self.detect_flatlines(
                    recording=recording,
                    start_seconds=start_seconds,
                    duration_seconds=duration_seconds,
                )
            )

        return candidates

    # =========================================================
    # High amplitude detector
    # =========================================================

    def detect_high_amplitude(
        self,
        recording: Recording,
        start_seconds: float,
        duration_seconds: float,
    ) -> list[ArtifactCandidate]:
        data, times = recording.get_window(
            start_seconds=start_seconds,
            duration_seconds=duration_seconds,
        )

        if data.size == 0:
            return []

        # MNE EEG is stored in volts.
        # Convert to microvolts.
        data_uv = data * 1_000_000

        threshold = self.thresholds.amplitude_uv

        candidates: list[ArtifactCandidate] = []

        for channel_index, channel_name in enumerate(
            recording.channels
        ):
            signal = data_uv[
                channel_index
            ]

            mask = (
                np.abs(signal)
                > threshold
            )

            regions = self._contiguous_regions(
                mask
            )

            for start_idx, end_idx in regions:
                if end_idx <= start_idx:
                    continue

                segment = signal[
                    start_idx:end_idx
                ]

                peak = float(
                    np.max(
                        np.abs(segment)
                    )
                )

                region_start = float(
                    times[start_idx]
                )

                final_index = min(
                    end_idx - 1,
                    len(times) - 1,
                )

                region_end = float(
                    times[final_index]
                )

                if region_end <= region_start:
                    region_end = (
                        region_start
                        + 1.0
                        / recording.sampling_frequency
                    )

                exceedance = (
                    peak / threshold
                )

                confidence = min(
                    1.0,
                    max(
                        0.1,
                        (
                            exceedance
                            - 1.0
                        )
                        / 1.5,
                    ),
                )

                candidate = ArtifactCandidate(
                    artifact_type=(
                        ArtifactType.HIGH_AMPLITUDE
                    ),
                    start_seconds=region_start,
                    end_seconds=region_end,
                    channels=[
                        channel_name
                    ],
                    confidence=confidence,
                    measured_value=peak,
                    threshold_value=threshold,
                    metric_name="Absolute amplitude",
                    unit="µV",
                    reason=(
                        f"{channel_name} exceeded the configured "
                        f"amplitude threshold of {threshold:.1f} µV. "
                        f"Peak amplitude reached {peak:.1f} µV."
                    ),
                )

                candidates.append(
                    candidate
                )

        return candidates

    # =========================================================
    # Rapid transient detector
    # =========================================================

    def detect_rapid_changes(
        self,
        recording: Recording,
        start_seconds: float,
        duration_seconds: float,
    ) -> list[ArtifactCandidate]:
        data, times = recording.get_window(
            start_seconds=start_seconds,
            duration_seconds=duration_seconds,
        )

        if data.size == 0:
            return []

        data_uv = data * 1_000_000

        threshold = (
            self.thresholds.rapid_change_uv
        )

        candidates: list[ArtifactCandidate] = []

        for channel_index, channel_name in enumerate(
            recording.channels
        ):
            signal = data_uv[
                channel_index
            ]

            if len(signal) < 2:
                continue

            delta = np.abs(
                np.diff(signal)
            )

            mask = (
                delta > threshold
            )

            regions = self._contiguous_regions(
                mask
            )

            for start_idx, end_idx in regions:
                if end_idx <= start_idx:
                    continue

                segment = delta[
                    start_idx:end_idx
                ]

                maximum_change = float(
                    np.max(segment)
                )

                time_index = min(
                    start_idx + 1,
                    len(times) - 1,
                )

                final_index = min(
                    end_idx + 1,
                    len(times) - 1,
                )

                region_start = float(
                    times[time_index]
                )

                region_end = float(
                    times[final_index]
                )

                if region_end <= region_start:
                    region_end = (
                        region_start
                        + 1.0
                        / recording.sampling_frequency
                    )

                exceedance = (
                    maximum_change
                    / threshold
                )

                confidence = min(
                    1.0,
                    max(
                        0.1,
                        (
                            exceedance
                            - 1.0
                        )
                        / 2.0,
                    ),
                )

                candidate = ArtifactCandidate(
                    artifact_type=(
                        ArtifactType.RAPID_CHANGE
                    ),
                    start_seconds=region_start,
                    end_seconds=region_end,
                    channels=[
                        channel_name
                    ],
                    confidence=confidence,
                    measured_value=maximum_change,
                    threshold_value=threshold,
                    metric_name=(
                        "Sample-to-sample change"
                    ),
                    unit="µV",
                    reason=(
                        f"{channel_name} showed a rapid voltage "
                        f"transition of {maximum_change:.1f} µV "
                        f"between consecutive samples. "
                        f"The configured threshold is "
                        f"{threshold:.1f} µV."
                    ),
                )

                candidates.append(
                    candidate
                )

        return candidates

    # =========================================================
    # Flatline detector
    # =========================================================

    def detect_flatlines(
        self,
        recording: Recording,
        start_seconds: float,
        duration_seconds: float,
    ) -> list[ArtifactCandidate]:
        data, times = recording.get_window(
            start_seconds=start_seconds,
            duration_seconds=duration_seconds,
        )

        if data.size == 0:
            return []

        data_uv = (
            data * 1_000_000
        )

        sfreq = (
            recording.sampling_frequency
        )

        minimum_seconds = (
            self.thresholds.flatline_seconds
        )

        tolerance = (
            self.thresholds.flatline_tolerance_uv
        )

        analysis_window_seconds = min(
            0.5,
            minimum_seconds,
        )

        analysis_window_samples = max(
            2,
            int(
                analysis_window_seconds
                * sfreq
            ),
        )

        step_samples = max(
            1,
            analysis_window_samples // 2,
        )

        minimum_samples = max(
            1,
            int(
                minimum_seconds
                * sfreq
            ),
        )

        candidates: list[ArtifactCandidate] = []

        for channel_index, channel_name in enumerate(
            recording.channels
        ):
            signal = data_uv[
                channel_index
            ]

            if len(signal) < minimum_samples:
                continue

            possible_regions: list[
                tuple[int, int, float]
            ] = []

            start_idx = 0

            while (
                start_idx
                + analysis_window_samples
                <= len(signal)
            ):
                end_idx = (
                    start_idx
                    + analysis_window_samples
                )

                segment = signal[
                    start_idx:end_idx
                ]

                peak_to_peak = float(
                    np.ptp(segment)
                )

                if peak_to_peak <= tolerance:
                    possible_regions.append(
                        (
                            start_idx,
                            end_idx,
                            peak_to_peak,
                        )
                    )

                start_idx += (
                    step_samples
                )

            if not possible_regions:
                continue

            merged_regions = (
                self._merge_sample_regions(
                    possible_regions
                )
            )

            for (
                region_start_idx,
                region_end_idx,
                region_peak_to_peak,
            ) in merged_regions:
                region_length = (
                    region_end_idx
                    - region_start_idx
                )

                if region_length < minimum_samples:
                    continue

                final_index = min(
                    region_end_idx - 1,
                    len(times) - 1,
                )

                region_start = float(
                    times[
                        region_start_idx
                    ]
                )

                region_end = float(
                    times[
                        final_index
                    ]
                )

                actual_duration = (
                    region_end
                    - region_start
                )

                candidate = ArtifactCandidate(
                    artifact_type=(
                        ArtifactType.FLATLINE
                    ),
                    start_seconds=region_start,
                    end_seconds=region_end,
                    channels=[
                        channel_name
                    ],
                    confidence=0.8,
                    measured_value=(
                        region_peak_to_peak
                    ),
                    threshold_value=tolerance,
                    metric_name=(
                        "Peak-to-peak amplitude"
                    ),
                    unit="µV",
                    reason=(
                        f"{channel_name} remained nearly flat "
                        f"for {actual_duration:.2f} seconds. "
                        f"Peak-to-peak variation was "
                        f"{region_peak_to_peak:.2f} µV, "
                        f"within the configured "
                        f"{tolerance:.2f} µV tolerance."
                    ),
                )

                candidates.append(
                    candidate
                )

        return candidates

    # =========================================================
    # Merge candidates
    # =========================================================

    def _merge_candidates(
        self,
        candidates: list[ArtifactCandidate],
        merge_gap_seconds: float,
    ) -> list[ArtifactCandidate]:
        if not candidates:
            return []

        ordered = sorted(
            candidates,
            key=lambda candidate: (
                (
                    candidate.channels[0]
                    if candidate.channels
                    else ""
                ),
                candidate.artifact_type.value,
                candidate.start_seconds,
            ),
        )

        merged: list[ArtifactCandidate] = []

        for candidate in ordered:
            if not merged:
                merged.append(
                    candidate
                )

                continue

            previous = (
                merged[-1]
            )

            same_channel = (
                previous.channels
                == candidate.channels
            )

            same_type = (
                previous.artifact_type
                == candidate.artifact_type
            )

            gap = (
                candidate.start_seconds
                - previous.end_seconds
            )

            if (
                same_channel
                and same_type
                and gap <= merge_gap_seconds
            ):
                previous.end_seconds = max(
                    previous.end_seconds,
                    candidate.end_seconds,
                )

                previous_value = (
                    previous.measured_value
                )

                candidate_value = (
                    candidate.measured_value
                )

                if (
                    previous.artifact_type
                    == ArtifactType.FLATLINE
                ):
                    if (
                        previous_value is None
                        or (
                            candidate_value is not None
                            and candidate_value
                            < previous_value
                        )
                    ):
                        previous.measured_value = (
                            candidate_value
                        )

                else:
                    if (
                        previous_value is None
                        or (
                            candidate_value is not None
                            and candidate_value
                            > previous_value
                        )
                    ):
                        previous.measured_value = (
                            candidate_value
                        )

            else:
                merged.append(
                    candidate
                )

        for candidate in merged:
            self._refresh_reason(
                candidate
            )

        return merged

    def _refresh_reason(
        self,
        candidate: ArtifactCandidate,
    ):
        channel = (
            candidate.channels[0]
            if candidate.channels
            else "Unknown channel"
        )

        if (
            candidate.artifact_type
            == ArtifactType.HIGH_AMPLITUDE
        ):
            candidate.reason = (
                f"{channel} exceeded the configured "
                f"amplitude threshold of "
                f"{candidate.threshold_value:.1f} µV. "
                f"Peak amplitude reached "
                f"{candidate.measured_value:.1f} µV."
            )

        elif (
            candidate.artifact_type
            == ArtifactType.RAPID_CHANGE
        ):
            candidate.reason = (
                f"{channel} showed a rapid voltage "
                f"transition of "
                f"{candidate.measured_value:.1f} µV "
                f"between consecutive samples. "
                f"The configured threshold is "
                f"{candidate.threshold_value:.1f} µV."
            )

        elif (
            candidate.artifact_type
            == ArtifactType.FLATLINE
        ):
            duration = (
                candidate.end_seconds
                - candidate.start_seconds
            )

            candidate.reason = (
                f"{channel} remained nearly flat for "
                f"{duration:.2f} seconds. "
                f"Peak-to-peak variation fell to "
                f"{candidate.measured_value:.2f} µV "
                f"within the configured "
                f"{candidate.threshold_value:.2f} µV "
                f"tolerance."
            )

    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _contiguous_regions(
        mask: np.ndarray,
    ) -> list[tuple[int, int]]:
        if len(mask) == 0:
            return []

        changes = np.diff(
            mask.astype(
                np.int8
            )
        )

        starts = list(
            np.where(
                changes == 1
            )[0]
            + 1
        )

        ends = list(
            np.where(
                changes == -1
            )[0]
            + 1
        )

        if mask[0]:
            starts.insert(
                0,
                0,
            )

        if mask[-1]:
            ends.append(
                len(mask)
            )

        return list(
            zip(
                starts,
                ends,
            )
        )

    @staticmethod
    def _merge_sample_regions(
        regions: list[
            tuple[int, int, float]
        ],
    ) -> list[
        tuple[int, int, float]
    ]:
        if not regions:
            return []

        merged: list[
            tuple[int, int, float]
        ] = []

        current_start = (
            regions[0][0]
        )

        current_end = (
            regions[0][1]
        )

        minimum_peak_to_peak = (
            regions[0][2]
        )

        for (
            start_idx,
            end_idx,
            peak_to_peak,
        ) in regions[1:]:
            if start_idx <= current_end:
                current_end = max(
                    current_end,
                    end_idx,
                )

                minimum_peak_to_peak = min(
                    minimum_peak_to_peak,
                    peak_to_peak,
                )

            else:
                merged.append(
                    (
                        current_start,
                        current_end,
                        minimum_peak_to_peak,
                    )
                )

                current_start = start_idx
                current_end = end_idx

                minimum_peak_to_peak = (
                    peak_to_peak
                )

        merged.append(
            (
                current_start,
                current_end,
                minimum_peak_to_peak,
            )
        )

        return merged