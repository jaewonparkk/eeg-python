from pathlib import Path

from synaptix.models.pipeline import (
    PipelineConfiguration,
    StepType,
)


def generate_pipeline_script(
    pipeline: PipelineConfiguration,
    input_path: Path | None = None,
) -> str:
    if input_path is None:
        input_path = Path(
            "recording.set"
        )

    lines: list[str] = [
        "from pathlib import Path",
        "",
        "import mne",
        "",
        "",
        f"INPUT_PATH = Path({str(input_path)!r})",
        "",
    ]

    # =========================================================
    # Loader
    # =========================================================

    suffix = (
        input_path.suffix.lower()
    )

    if suffix == ".set":
        lines.extend(
            [
                "raw = mne.io.read_raw_eeglab(",
                "    INPUT_PATH,",
                "    preload=True,",
                ")",
            ]
        )

    elif suffix == ".edf":
        lines.extend(
            [
                "raw = mne.io.read_raw_edf(",
                "    INPUT_PATH,",
                "    preload=True,",
                ")",
            ]
        )

    elif suffix == ".bdf":
        lines.extend(
            [
                "raw = mne.io.read_raw_bdf(",
                "    INPUT_PATH,",
                "    preload=True,",
                ")",
            ]
        )

    elif suffix == ".fif":
        lines.extend(
            [
                "raw = mne.io.read_raw_fif(",
                "    INPUT_PATH,",
                "    preload=True,",
                ")",
            ]
        )

    else:
        lines.extend(
            [
                "# Replace this loader with the",
                "# appropriate MNE reader.",
                "raw = None",
            ]
        )

    lines.extend(
        [
            "",
            "",
            "# ========================================",
            "# Synaptix preprocessing pipeline",
            "# Executes from top to bottom",
            "# ========================================",
            "",
        ]
    )

    # =========================================================
    # Pipeline
    # =========================================================

    enabled_steps = (
        pipeline.enabled_steps()
    )

    if not enabled_steps:
        lines.append(
            "# No preprocessing steps enabled."
        )

    for index, step in enumerate(
        enabled_steps,
        start=1,
    ):
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

            lines.extend(
                [
                    f"# {index}. Band-pass Filter",
                    "raw.filter(",
                    f"    l_freq={highpass!r},",
                    f"    h_freq={lowpass!r},",
                    ")",
                    "",
                ]
            )

        elif (
            step.step_type
            == StepType.NOTCH
        ):
            frequency = float(
                step.parameters.get(
                    "frequency_hz",
                    60.0,
                )
            )

            lines.extend(
                [
                    f"# {index}. Notch Filter",
                    "raw.notch_filter(",
                    f"    freqs=[{frequency!r}],",
                    ")",
                    "",
                ]
            )

        elif (
            step.step_type
            == StepType.AVERAGE_REFERENCE
        ):
            excluded = list(
                step.parameters.get(
                    "exclude_channels",
                    [],
                )
            )

            lines.append(
                f"# {index}. Average Reference"
            )

            if excluded:
                lines.extend(
                    [
                        (
                            "excluded_reference_channels "
                            f"= {excluded!r}"
                        ),
                        "",
                        (
                            "eeg_channels = "
                            'raw.copy().pick("eeg").ch_names'
                        ),
                        "",
                        (
                            "reference_channels = ["
                        ),
                        "    channel",
                        "    for channel in eeg_channels",
                        (
                            "    if channel not in "
                            "excluded_reference_channels"
                        ),
                        "]",
                        "",
                        "raw.set_eeg_reference(",
                        (
                            "    ref_channels="
                            "reference_channels,"
                        ),
                        ")",
                        "",
                    ]
                )

            else:
                lines.extend(
                    [
                        "raw.set_eeg_reference(",
                        '    ref_channels="average",',
                        ")",
                        "",
                    ]
                )

    # =========================================================
    # Save
    # =========================================================

    lines.extend(
        [
            "",
            "OUTPUT_PATH = INPUT_PATH.with_name(",
            (
                '    INPUT_PATH.stem '
                '+ "_synaptix_raw.fif"'
            ),
            ")",
            "",
            "raw.save(",
            "    OUTPUT_PATH,",
            "    overwrite=True,",
            ")",
            "",
            'print(f"Saved: {OUTPUT_PATH}")',
        ]
    )

    return "\n".join(
        lines
    )