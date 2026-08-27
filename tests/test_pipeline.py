import ast
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


# =============================================================
# Helpers
# =============================================================


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


def extract_script_assignment(
    script: str,
    variable_name: str,
):
    """
    Safely extract a top-level literal assignment
    from the generated Python script.

    Example:
        PIPELINE_ORDER = [...]
    """

    tree = ast.parse(
        script
    )

    for node in tree.body:
        if not isinstance(
            node,
            ast.Assign,
        ):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if not isinstance(
            target,
            ast.Name,
        ):
            continue

        if target.id != variable_name:
            continue

        return ast.literal_eval(
            node.value
        )

    raise AssertionError(
        (
            f"{variable_name} was not "
            "found in generated script."
        )
    )


# =============================================================
# Basic processing
# =============================================================


def test_pipeline_preserves_shape():
    recording = (
        create_recording()
    )

    pipeline = (
        PipelineConfiguration.default()
    )

    engine = (
        EEGProcessingPipeline(
            configuration=pipeline
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
            ],
        )
    )

    assert (
        result.raw_data.shape
        == result.processed_data.shape
    )

    assert (
        result.raw_data.shape[0]
        == 2
    )

    assert (
        len(result.times)
        == result.raw_data.shape[1]
    )


# =============================================================
# Average reference
# =============================================================


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
            configuration=pipeline
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
                "F3",
            ],
        )
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


def test_average_reference_can_exclude_channel():
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
                        "exclude_channels": [
                            "Fp1"
                        ],
                    },
                )
            ]
        )
    )

    engine = (
        EEGProcessingPipeline(
            configuration=pipeline
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
                "F3",
            ],
        )
    )

    # Fp2 and F3 form the average reference.
    # Their mean should therefore be ~0.
    reference_channel_mean = (
        np.mean(
            result.processed_data[
                [
                    1,
                    2,
                ],
                :
            ],
            axis=0,
        )
    )

    assert np.allclose(
        reference_channel_mean,
        0.0,
        atol=1e-12,
    )


# =============================================================
# Pipeline order
# =============================================================


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

    pipeline_order = (
        extract_script_assignment(
            script=script,
            variable_name=(
                "PIPELINE_ORDER"
            ),
        )
    )

    assert pipeline_order == [
        "average_reference",
        "bandpass",
    ]


def test_default_generated_script_preserves_default_order():
    pipeline = (
        PipelineConfiguration.default()
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline,
            input_path=Path(
                "example.set"
            ),
        )
    )

    pipeline_order = (
        extract_script_assignment(
            script=script,
            variable_name=(
                "PIPELINE_ORDER"
            ),
        )
    )

    assert pipeline_order == [
        "bandpass",
        "notch",
        "average_reference",
    ]


# =============================================================
# Generated configuration
# =============================================================


def test_generated_script_contains_filter_settings():
    pipeline = (
        PipelineConfiguration.default()
    )

    bandpass = (
        pipeline.get_step(
            "bandpass"
        )
    )

    assert bandpass is not None

    bandpass.parameters[
        "highpass_hz"
    ] = 1.0

    bandpass.parameters[
        "lowpass_hz"
    ] = 40.0

    script = (
        generate_pipeline_script(
            pipeline=pipeline,
            input_path=Path(
                "example.set"
            ),
        )
    )

    highpass = (
        extract_script_assignment(
            script=script,
            variable_name=(
                "HIGHPASS_HZ"
            ),
        )
    )

    lowpass = (
        extract_script_assignment(
            script=script,
            variable_name=(
                "LOWPASS_HZ"
            ),
        )
    )

    assert highpass == 1.0
    assert lowpass == 40.0


def test_generated_script_contains_reference_settings():
    pipeline = (
        PipelineConfiguration.default()
    )

    reference = (
        pipeline.get_step(
            "average_reference"
        )
    )

    assert reference is not None

    reference.enabled = True

    reference.parameters[
        "exclude_channels"
    ] = [
        "Fp1",
        "Fp2",
    ]

    script = (
        generate_pipeline_script(
            pipeline=pipeline,
            input_path=Path(
                "example.set"
            ),
        )
    )

    enabled = (
        extract_script_assignment(
            script=script,
            variable_name=(
                "AVERAGE_REFERENCE_ENABLED"
            ),
        )
    )

    excluded = (
        extract_script_assignment(
            script=script,
            variable_name=(
                "REFERENCE_EXCLUDE"
            ),
        )
    )

    assert enabled is True

    assert excluded == [
        "Fp1",
        "Fp2",
    ]


# =============================================================
# Generated script validity
# =============================================================


def test_generated_script_is_valid_python():
    pipeline = (
        PipelineConfiguration.default()
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline,
            input_path=Path(
                "example.set"
            ),
        )
    )

    # Raises SyntaxError if generated code is invalid.
    ast.parse(
        script
    )