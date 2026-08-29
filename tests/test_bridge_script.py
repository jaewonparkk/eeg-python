from pathlib import Path

from synaptix.models.bridge import (
    BridgeDetectionSettings,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
)
from synaptix.processing.script_generator import (
    generate_pipeline_script,
)
from synaptix.processing.script_parser import (
    parse_bridge_settings,
    parse_confirmed_bridges,
)


def test_bridge_settings_round_trip():
    pipeline = (
        PipelineConfiguration.default()
    )

    settings = (
        BridgeDetectionSettings(
            lm_cutoff_uv2=12.0,
            epoch_threshold=0.6,
            low_frequency_hz=1.0,
            high_frequency_hz=25.0,
            epoch_duration_seconds=3.0,
        )
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline,
            input_path=Path(
                "example.set"
            ),
            bridge_settings=(
                settings
            ),
        )
    )

    parsed = (
        parse_bridge_settings(
            script=script,
            current_settings=(
                BridgeDetectionSettings()
            ),
        )
    )

    assert (
        parsed.lm_cutoff_uv2
        == 12.0
    )

    assert (
        parsed.epoch_threshold
        == 0.6
    )

    assert (
        parsed.low_frequency_hz
        == 1.0
    )

    assert (
        parsed.high_frequency_hz
        == 25.0
    )

    assert (
        parsed.epoch_duration_seconds
        == 3.0
    )


def test_confirmed_bridges_round_trip():
    pipeline = (
        PipelineConfiguration.default()
    )

    script = (
        generate_pipeline_script(
            pipeline=pipeline,
            confirmed_bridges=[
                (
                    "Fp1",
                    "Fp2",
                ),
                (
                    "F3",
                    "F4",
                ),
            ],
        )
    )

    parsed = (
        parse_confirmed_bridges(
            script
        )
    )

    assert parsed == [
        (
            "Fp1",
            "Fp2",
        ),
        (
            "F3",
            "F4",
        ),
    ]