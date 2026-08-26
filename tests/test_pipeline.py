from pathlib import Path

import mne
import numpy as np

from synaptix.core.recording import (
    Recording,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
    PipelineStep,
    StepType,
)
from synaptix.processing.pipeline import (
    EEGProcessingPipeline,
)
from synaptix.processing.script_generator import (
    generate_pipeline_script,
)


def create_recording(
    duration_seconds: float = 10.0,
) -> Recording:
    sfreq = 500.0

    times = np.arange(
        0,
        duration_seconds,
        1 / sfreq,
    )

    common = (
        20e-6
        * np.sin(
            2
            * np.pi
            * 10
            * times
        )
    )

    noise_60 = (
        15e-6
        * np.sin(
            2
            * np.pi
            * 60
            * times
        )
    )

    data = np.vstack(
        [
            common + noise_60,
            common * 0.8 + noise_60,
            common * 1.2 + noise_60,
        ]
    )

    info = mne.create_info(
        ch_names=[
            "Fp1",
            "Fp2",
            "F3",
        ],
        sfreq=sfreq,
        ch_types=[
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
            "synthetic.fif"
        ),
    )


def test_pipeline_preserves_shape():
    recording = (
        create_recording()
    )

    pipeline = (
        PipelineConfiguration.default()
    )

    engine = (
        EEGProcessingPipeline(
            pipeline
        )
    )

    result = engine.process_window(
        recording=recording,
        start_seconds=2.0,
        duration_seconds=5.0,
        channels=[
            "Fp1",
            "Fp2",
        ],
    )

    assert (
        result.raw_data.shape
        == result.processed_data.shape
    )

    assert (
        result.raw_data.shape[0]
        == 2
    )


def test_average_reference_has_zero_channel_mean():
    recording = (
        create_recording()
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
            pipeline
        )
    )

    result = engine.process_window(
        recording=recording,
        start_seconds=2.0,
        duration_seconds=5.0,
        channels=[
            "Fp1",
            "Fp2",
            "F3",
        ],
    )

    channel_mean = np.mean(
        result.processed_data,
        axis=0,
    )

    assert np.allclose(
        channel_mean,
        0.0,
        atol=1e-12,
    )


def test_generated_script_preserves_pipeline_order():
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
                ),
                PipelineStep(
                    step_id="bandpass",
                    step_type=(
                        StepType.BANDPASS
                    ),
                    enabled=True,
                    parameters={
                        "highpass_hz": 1.0,
                        "lowpass_hz": 40.0,
                        "order": 4,
                    },
                ),
            ]
        )
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline,
            input_path=Path(
                "example.set"
            ),
        )
    )

    reference_position = (
        script.index(
            "set_eeg_reference"
        )
    )

    filter_position = (
        script.index(
            "raw.filter"
        )
    )

    assert (
        reference_position
        < filter_position
    )