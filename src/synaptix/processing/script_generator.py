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

    bandpass = pipeline.get_step(
        "bandpass"
    )

    notch = pipeline.get_step(
        "notch"
    )

    reference = pipeline.get_step(
        "average_reference"
    )

    # =========================================================
    # Current configuration
    # =========================================================

    bandpass_enabled = (
        bandpass.enabled
        if bandpass is not None
        else False
    )

    highpass_hz = float(
        (
            bandpass.parameters.get(
                "highpass_hz",
                0.5,
            )
            if bandpass is not None
            else 0.5
        )
    )

    lowpass_hz = float(
        (
            bandpass.parameters.get(
                "lowpass_hz",
                45.0,
            )
            if bandpass is not None
            else 45.0
        )
    )

    filter_order = int(
        (
            bandpass.parameters.get(
                "order",
                4,
            )
            if bandpass is not None
            else 4
        )
    )

    notch_enabled = (
        notch.enabled
        if notch is not None
        else False
    )

    notch_hz = float(
        (
            notch.parameters.get(
                "frequency_hz",
                60.0,
            )
            if notch is not None
            else 60.0
        )
    )

    notch_q = float(
        (
            notch.parameters.get(
                "quality_factor",
                30.0,
            )
            if notch is not None
            else 30.0
        )
    )

    reference_enabled = (
        reference.enabled
        if reference is not None
        else False
    )

    reference_exclude = list(
        (
            reference.parameters.get(
                "exclude_channels",
                [],
            )
            if reference is not None
            else []
        )
    )

    pipeline_order = [
        step.step_id
        for step in pipeline.steps
    ]

    # =========================================================
    # Generate runnable Python script
    # =========================================================

    lines = [
        "from pathlib import Path",
        "",
        "import mne",
        "",
        "",
        "# ========================================================",
        "# SYNAPTIX PIPELINE CONFIGURATION",
        "#",
        "# You can edit the values in this section and then",
        "# paste/apply this script back into Synaptix.",
        "# ========================================================",
        "",
        f"INPUT_PATH = Path({str(input_path)!r})",
        "",
        f"PIPELINE_ORDER = {pipeline_order!r}",
        "",
        f"BANDPASS_ENABLED = {bandpass_enabled!r}",
        f"HIGHPASS_HZ = {highpass_hz!r}",
        f"LOWPASS_HZ = {lowpass_hz!r}",
        f"FILTER_ORDER = {filter_order!r}",
        "",
        f"NOTCH_ENABLED = {notch_enabled!r}",
        f"NOTCH_HZ = {notch_hz!r}",
        f"NOTCH_Q = {notch_q!r}",
        "",
        (
            "AVERAGE_REFERENCE_ENABLED = "
            f"{reference_enabled!r}"
        ),
        (
            "REFERENCE_EXCLUDE = "
            f"{reference_exclude!r}"
        ),
        "",
        "",
        "# ========================================================",
        "# LOAD EEG",
        "# ========================================================",
        "",
        "",
        "def load_raw(path: Path):",
        "    suffix = path.suffix.lower()",
        "",
        '    if suffix == ".set":',
        "        return mne.io.read_raw_eeglab(",
        "            path,",
        "            preload=True,",
        "            verbose=False,",
        "        )",
        "",
        '    if suffix == ".edf":',
        "        return mne.io.read_raw_edf(",
        "            path,",
        "            preload=True,",
        "            verbose=False,",
        "        )",
        "",
        '    if suffix == ".bdf":',
        "        return mne.io.read_raw_bdf(",
        "            path,",
        "            preload=True,",
        "            verbose=False,",
        "        )",
        "",
        '    if suffix == ".fif":',
        "        return mne.io.read_raw_fif(",
        "            path,",
        "            preload=True,",
        "            verbose=False,",
        "        )",
        "",
        "    raise ValueError(",
        '        f"Unsupported EEG format: {suffix}"',
        "    )",
        "",
        "",
        "# ========================================================",
        "# PIPELINE FUNCTIONS",
        "# ========================================================",
        "",
        "",
        "def apply_bandpass(raw):",
        "    if not BANDPASS_ENABLED:",
        "        return raw",
        "",
        "    raw.filter(",
        "        l_freq=HIGHPASS_HZ,",
        "        h_freq=LOWPASS_HZ,",
        "        verbose=False,",
        "    )",
        "",
        "    return raw",
        "",
        "",
        "def apply_notch(raw):",
        "    if not NOTCH_ENABLED:",
        "        return raw",
        "",
        "    raw.notch_filter(",
        "        freqs=[NOTCH_HZ],",
        "        verbose=False,",
        "    )",
        "",
        "    return raw",
        "",
        "",
        "def apply_average_reference(raw):",
        "    if not AVERAGE_REFERENCE_ENABLED:",
        "        return raw",
        "",
        "    if REFERENCE_EXCLUDE:",
        "        eeg_channels = (",
        "            raw.copy()",
        '            .pick("eeg")',
        "            .ch_names",
        "        )",
        "",
        "        reference_channels = [",
        "            channel",
        "            for channel in eeg_channels",
        "            if channel not in REFERENCE_EXCLUDE",
        "        ]",
        "",
        "        if len(reference_channels) < 2:",
        "            raise ValueError(",
        '                "Average reference requires at least "',
        '                "two eligible EEG channels."',
        "            )",
        "",
        "        raw.set_eeg_reference(",
        "            ref_channels=reference_channels,",
        "            verbose=False,",
        "        )",
        "",
        "    else:",
        "        raw.set_eeg_reference(",
        '            ref_channels="average",',
        "            verbose=False,",
        "        )",
        "",
        "    return raw",
        "",
        "",
        "# ========================================================",
        "# PIPELINE EXECUTION",
        "# ========================================================",
        "",
        "",
        "STEP_FUNCTIONS = {",
        '    "bandpass": apply_bandpass,',
        '    "notch": apply_notch,',
        '    "average_reference": apply_average_reference,',
        "}",
        "",
        "",
        "def run_pipeline(raw):",
        "    for step_name in PIPELINE_ORDER:",
        "        if step_name not in STEP_FUNCTIONS:",
        "            raise ValueError(",
        "                f\"Unknown pipeline step: {step_name}\"",
        "            )",
        "",
        "        raw = STEP_FUNCTIONS[step_name](",
        "            raw",
        "        )",
        "",
        "    return raw",
        "",
        "",
        "# ========================================================",
        "# MAIN",
        "# ========================================================",
        "",
        "",
        "raw = load_raw(",
        "    INPUT_PATH",
        ")",
        "",
        "raw = run_pipeline(",
        "    raw",
        ")",
        "",
        "OUTPUT_PATH = INPUT_PATH.with_name(",
        "    INPUT_PATH.stem",
        '    + "_synaptix_raw.fif"',
        ")",
        "",
        "raw.save(",
        "    OUTPUT_PATH,",
        "    overwrite=True,",
        ")",
        "",
        'print(f"Saved processed EEG to: {OUTPUT_PATH}")',
    ]

    return "\n".join(
        lines
    )