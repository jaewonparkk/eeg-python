from pathlib import Path

import mne
import numpy as np

from synaptix.analysis.channel_quality import (
    ChannelQualityAnalyzer,
)
from synaptix.core.recording import (
    Recording,
)
from synaptix.models.channel_quality import (
    ChannelQualityThresholds,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
    PipelineStep,
    StepType,
)
from synaptix.processing.pipeline import (
    EEGProcessingPipeline,
)


def create_quality_recording() -> Recording:
    sampling_frequency = (
        500.0
    )

    duration_seconds = (
        10.0
    )

    times = np.arange(
        0,
        duration_seconds,
        (
            1.0
            / sampling_frequency
        ),
    )

    normal = (
        20e-6
        * np.sin(
            2
            * np.pi
            * 10
            * times
        )
    )

    second_normal = (
        18e-6
        * np.sin(
            2
            * np.pi
            * 10
            * times
            + 0.1
        )
    )

    flat = np.zeros_like(
        times
    )

    noisy = (
        350e-6
        * np.sin(
            2
            * np.pi
            * 25
            * times
        )
    )

    data = np.vstack(
        [
            normal,
            second_normal,
            flat,
            noisy,
        ]
    )

    info = mne.create_info(
        ch_names=[
            "Fp1",
            "Fp2",
            "Flat",
            "Noisy",
        ],
        sfreq=(
            sampling_frequency
        ),
        ch_types=[
            "eeg",
            "eeg",
            "eeg",
            "eeg",
        ],
    )

    raw = mne.io.RawArray(
        data,
        info,
        verbose=False,
    )

    return Recording(
        raw=raw,
        source_path=Path(
            "quality_test.fif"
        ),
    )


def test_channel_quality_flags_flat_channel():
    recording = (
        create_quality_recording()
    )

    analyzer = (
        ChannelQualityAnalyzer(
            thresholds=(
                ChannelQualityThresholds()
            )
        )
    )

    results = (
        analyzer.analyze_recording(
            recording
        )
    )

    result_map = {
        result.channel: result
        for result in results
    }

    flat = result_map[
        "Flat"
    ]

    assert flat.flagged is True

    assert (
        flat.flat_fraction
        >= 0.9
    )


def test_channel_quality_flags_noisy_channel():
    recording = (
        create_quality_recording()
    )

    analyzer = (
        ChannelQualityAnalyzer(
            thresholds=(
                ChannelQualityThresholds()
            )
        )
    )

    results = (
        analyzer.analyze_recording(
            recording
        )
    )

    result_map = {
        result.channel: result
        for result in results
    }

    noisy = result_map[
        "Noisy"
    ]

    assert noisy.flagged is True

    assert (
        noisy.extreme_fraction
        > 0
    )


def test_mark_and_unmark_bad_channel():
    recording = (
        create_quality_recording()
    )

    recording.mark_bad_channel(
        "Fp1"
    )

    assert (
        "Fp1"
        in recording.bad_channels
    )

    recording.mark_good_channel(
        "Fp1"
    )

    assert (
        "Fp1"
        not in recording.bad_channels
    )


def test_average_reference_excludes_marked_bad_channel():
    recording = (
        create_quality_recording()
    )

    recording.mark_bad_channel(
        "Fp1"
    )

    pipeline = (
        PipelineConfiguration(
            steps=[
                PipelineStep(
                    step_id=(
                        "average_reference"
                    ),
                    step_type=(
                        StepType.AVERAGE_REFERENCE
                    ),
                    enabled=True,
                    parameters={
                        "exclude_channels": [],
                    },
                )
            ]
        )
    )

    engine = (
        EEGProcessingPipeline(
            configuration=(
                pipeline
            )
        )
    )

    result = (
        engine.process_window(
            recording=recording,
            start_seconds=2.0,
            duration_seconds=5.0,
            channels=[
                "Fp1",
                "Fp2",
                "Flat",
                "Noisy",
            ],
        )
    )

    # Marked bad channel should remain unchanged.
    assert np.allclose(
        result.processed_data[
            0
        ],
        result.raw_data[
            0
        ],
        atol=1e-12,
    )

    # Mean across eligible GOOD channels
    # should be approximately zero.
    good_mean = np.mean(
        result.processed_data[
            [
                1,
                2,
                3,
            ],
            :
        ],
        axis=0,
    )

    assert np.allclose(
        good_mean,
        0.0,
        atol=1e-12,
    )