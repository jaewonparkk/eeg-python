from collections.abc import Callable

import numpy as np

from synaptix.core.recording import Recording
from synaptix.models.artifact import (
    ArtifactCandidate,
    ArtifactType,
)
from synaptix.models.thresholds import DetectionThresholds


class ArtifactDetector:
    def __init__(
        self,
        thresholds: DetectionThresholds,
    ):
        self.thresholds = thresholds

    def detect_recording(
        self,
        recording: Recording,
        chunk_seconds: float = 30.0,
        progress_callback: Callable[[int], None] | None = None,
    ) -> list[ArtifactCandidate]:
        """
        Scan the full recording without loading the entire EEG into memory.

        The recording is processed in fixed-size chunks so this can later
        scale to multi-hour EEG recordings.
        """

        all_candidates: list[ArtifactCandidate] = []

        total_duration = recording.duration_seconds

        if total_duration <= 0:
            return []

        current_start = 0.0

        while current_start < total_duration:
            duration = min(
                chunk_seconds,
                total_duration - current_start,
            )

            candidates = self.detect_amplitude_artifacts(
                recording=recording,
                start_seconds=current_start,
                duration_seconds=duration,
            )

            all_candidates.extend(candidates)

            current_start += duration

            if progress_callback is not None:
                progress = int(
                    min(
                        100,
                        (current_start / total_duration) * 100,
                    )
                )

                progress_callback(progress)

        return self._merge_candidates(
            all_candidates,
            merge_gap_seconds=0.25,
        )

    def detect_amplitude_artifacts(
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

        # MNE EEG units are volts.
        data_uv = data * 1_000_000

        threshold = self.thresholds.amplitude_uv

        candidates: list[ArtifactCandidate] = []

        for channel_index, channel_name in enumerate(
            recording.channels
        ):
            signal = data_uv[channel_index]

            mask = np.abs(signal) > threshold

            if not np.any(mask):
                continue

            regions = self._contiguous_regions(mask)

            for start_idx, end_idx in regions:
                if end_idx <= start_idx:
                    continue

                region_signal = signal[
                    start_idx:end_idx
                ]

                peak = float(
                    np.max(
                        np.abs(region_signal)
                    )
                )

                start_time = float(
                    times[start_idx]
                )

                final_index = min(
                    end_idx - 1,
                    len(times) - 1,
                )

                end_time = float(
                    times[final_index]
                )

                # Avoid zero-width graphical regions.
                if end_time <= start_time:
                    end_time = (
                        start_time
                        + 1.0
                        / recording.sampling_frequency
                    )

                exceedance_ratio = (
                    peak / threshold
                )

                confidence = min(
                    1.0,
                    max(
                        0.0,
                        (exceedance_ratio - 1.0)
                        / 1.5,
                    ),
                )

                candidates.append(
                    ArtifactCandidate(
                        artifact_type=(
                            ArtifactType.HIGH_AMPLITUDE
                        ),
                        start_seconds=start_time,
                        end_seconds=end_time,
                        channels=[channel_name],
                        confidence=confidence,
                        measured_value=peak,
                        threshold_value=threshold,
                        reason=(
                            f"{channel_name} exceeded the "
                            f"{threshold:.0f} µV amplitude threshold. "
                            f"Peak amplitude reached {peak:.1f} µV."
                        ),
                    )
                )

        return candidates

    def _merge_candidates(
        self,
        candidates: list[ArtifactCandidate],
        merge_gap_seconds: float,
    ) -> list[ArtifactCandidate]:
        """
        Merge nearby detections from the same channel/type.

        Without this, one artifact may appear as many tiny candidate
        regions when the signal repeatedly crosses the threshold.
        """

        if not candidates:
            return []

        candidates = sorted(
            candidates,
            key=lambda candidate: (
                candidate.channels[0],
                candidate.artifact_type.value,
                candidate.start_seconds,
            ),
        )

        merged: list[ArtifactCandidate] = []

        for candidate in candidates:
            if not merged:
                merged.append(candidate)
                continue

            previous = merged[-1]

            same_channel = (
                previous.channels
                == candidate.channels
            )

            same_type = (
                previous.artifact_type
                == candidate.artifact_type
            )

            close_enough = (
                candidate.start_seconds
                - previous.end_seconds
                <= merge_gap_seconds
            )

            if (
                same_channel
                and same_type
                and close_enough
            ):
                previous.end_seconds = max(
                    previous.end_seconds,
                    candidate.end_seconds,
                )

                previous_peak = (
                    previous.measured_value
                    or 0.0
                )

                candidate_peak = (
                    candidate.measured_value
                    or 0.0
                )

                if candidate_peak > previous_peak:
                    previous.measured_value = (
                        candidate_peak
                    )

                previous.reason = (
                    f"{previous.channels[0]} exceeded "
                    f"the {previous.threshold_value:.0f} µV "
                    f"amplitude threshold. "
                    f"Peak amplitude reached "
                    f"{previous.measured_value:.1f} µV."
                )

            else:
                merged.append(candidate)

        return merged

    @staticmethod
    def _contiguous_regions(
        mask: np.ndarray,
    ) -> list[tuple[int, int]]:

        if len(mask) == 0:
            return []

        changes = np.diff(
            mask.astype(np.int8)
        )

        starts = list(
            np.where(changes == 1)[0] + 1
        )

        ends = list(
            np.where(changes == -1)[0] + 1
        )

        if mask[0]:
            starts.insert(0, 0)

        if mask[-1]:
            ends.append(len(mask))

        return list(
            zip(starts, ends)
        )