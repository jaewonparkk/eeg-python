from pathlib import Path

from synaptix.models.pipeline import (
    PipelineConfiguration,
)
from synaptix.processing.script_generator import (
    generate_pipeline_script,
)
from synaptix.processing.script_parser import (
    parse_pipeline_script,
)


def test_generated_script_round_trip():
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

    parsed = (
        parse_pipeline_script(
            script=script,
            current_pipeline=pipeline,
        )
    )

    assert [
        step.step_id
        for step in parsed.steps
    ] == [
        step.step_id
        for step in pipeline.steps
    ]


def test_script_can_change_filter_settings():
    pipeline = (
        PipelineConfiguration.default()
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline
        )
    )

    script = script.replace(
        "HIGHPASS_HZ = 0.5",
        "HIGHPASS_HZ = 1.0",
    )

    script = script.replace(
        "LOWPASS_HZ = 45.0",
        "LOWPASS_HZ = 40.0",
    )

    parsed = (
        parse_pipeline_script(
            script=script,
            current_pipeline=pipeline,
        )
    )

    bandpass = parsed.get_step(
        "bandpass"
    )

    assert bandpass is not None

    assert (
        bandpass.parameters[
            "highpass_hz"
        ]
        == 1.0
    )

    assert (
        bandpass.parameters[
            "lowpass_hz"
        ]
        == 40.0
    )


def test_script_can_change_pipeline_order():
    pipeline = (
        PipelineConfiguration.default()
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline
        )
    )

    original = (
        "PIPELINE_ORDER = "
        "['bandpass', 'notch', "
        "'average_reference']"
    )

    replacement = (
        "PIPELINE_ORDER = "
        "['average_reference', "
        "'bandpass', 'notch']"
    )

    script = script.replace(
        original,
        replacement,
    )

    parsed = (
        parse_pipeline_script(
            script=script,
            current_pipeline=pipeline,
        )
    )

    assert [
        step.step_id
        for step in parsed.steps
    ] == [
        "average_reference",
        "bandpass",
        "notch",
    ]


def test_script_can_enable_average_reference():
    pipeline = (
        PipelineConfiguration.default()
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline
        )
    )

    script = script.replace(
        (
            "AVERAGE_REFERENCE_ENABLED "
            "= False"
        ),
        (
            "AVERAGE_REFERENCE_ENABLED "
            "= True"
        ),
    )

    parsed = (
        parse_pipeline_script(
            script=script,
            current_pipeline=pipeline,
        )
    )

    reference = parsed.get_step(
        "average_reference"
    )

    assert reference is not None
    assert reference.enabled is True


def test_invalid_filter_range_is_rejected():
    pipeline = (
        PipelineConfiguration.default()
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline
        )
    )

    script = script.replace(
        "HIGHPASS_HZ = 0.5",
        "HIGHPASS_HZ = 50.0",
    )

    script = script.replace(
        "LOWPASS_HZ = 45.0",
        "LOWPASS_HZ = 40.0",
    )

    try:
        parse_pipeline_script(
            script=script,
            current_pipeline=pipeline,
        )

    except ValueError:
        return

    raise AssertionError(
        (
            "Invalid frequency range "
            "should raise ValueError."
        )
    )