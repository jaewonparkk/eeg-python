from pathlib import Path

from synaptix.models.bridge import (
    BridgeDetectionSettings,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
)


def generate_pipeline_script(
    pipeline: PipelineConfiguration,
    input_path: Path | None = None,
    bad_channels: list[str] | None = None,
    bridge_settings: BridgeDetectionSettings | None = None,
    confirmed_bridges: list[
        tuple[str, str]
    ]
    | None = None,
) -> str:
    if input_path is None:
        input_path = Path(
            "recording.set"
        )

    if bad_channels is None:
        bad_channels = []

    if bridge_settings is None:
        bridge_settings = (
            BridgeDetectionSettings()
        )

    if confirmed_bridges is None:
        confirmed_bridges = []

    bandpass = pipeline.get_step(
        "bandpass"
    )

    notch = pipeline.get_step(
        "notch"
    )

    reference = pipeline.get_step(
        "average_reference"
    )

    bandpass_enabled = (
        bandpass.enabled
        if bandpass is not None
        else False
    )

    highpass_hz = float(
        bandpass.parameters.get(
            "highpass_hz",
            0.5,
        )
        if bandpass is not None
        else 0.5
    )

    lowpass_hz = float(
        bandpass.parameters.get(
            "lowpass_hz",
            45.0,
        )
        if bandpass is not None
        else 45.0
    )

    filter_order = int(
        bandpass.parameters.get(
            "order",
            4,
        )
        if bandpass is not None
        else 4
    )

    notch_enabled = (
        notch.enabled
        if notch is not None
        else False
    )

    notch_hz = float(
        notch.parameters.get(
            "frequency_hz",
            60.0,
        )
        if notch is not None
        else 60.0
    )

    notch_q = float(
        notch.parameters.get(
            "quality_factor",
            30.0,
        )
        if notch is not None
        else 30.0
    )

    reference_enabled = (
        reference.enabled
        if reference is not None
        else False
    )

    reference_exclude = list(
        reference.parameters.get(
            "exclude_channels",
            [],
        )
        if reference is not None
        else []
    )

    pipeline_order = [
        step.step_id
        for step in pipeline.steps
    ]

    lines = [
        "from pathlib import Path",
        "",
        "import mne",
        "",
        "",
        "# ========================================================",
        "# SYNAPTIX CONFIGURATION",
        "# ========================================================",
        "",
        f"INPUT_PATH = Path({str(input_path)!r})",
        "",
        f"PIPELINE_ORDER = {pipeline_order!r}",
        "",
        f"BAD_CHANNELS = {bad_channels!r}",
        "",
        (
            "BRIDGE_DETECTION_ENABLED = "
            f"{bridge_settings.enabled!r}"
        ),
        (
            "BRIDGE_LM_CUTOFF_UV2 = "
            f"{bridge_settings.lm_cutoff_uv2!r}"
        ),
        (
            "BRIDGE_EPOCH_THRESHOLD = "
            f"{bridge_settings.epoch_threshold!r}"
        ),
        (
            "BRIDGE_L_FREQ = "
            f"{bridge_settings.low_frequency_hz!r}"
        ),
        (
            "BRIDGE_H_FREQ = "
            f"{bridge_settings.high_frequency_hz!r}"
        ),
        (
            "BRIDGE_EPOCH_DURATION = "
            f"{bridge_settings.epoch_duration_seconds!r}"
        ),
        (
            "CONFIRMED_BRIDGES = "
            f"{confirmed_bridges!r}"
        ),
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
        "# BRIDGE ANALYSIS",
        "# ========================================================",
        "",
        "",
        "def detect_bridges(raw):",
        "    if not BRIDGE_DETECTION_ENABLED:",
        "        return []",
        "",
        "    eeg_raw = (",
        "        raw.copy()",
        '        .pick("eeg")',
        "    )",
        "",
        "    bridged_idx, _ = (",
        "        mne.preprocessing",
        "        .compute_bridged_electrodes(",
        "            eeg_raw,",
        "            lm_cutoff=BRIDGE_LM_CUTOFF_UV2,",
        "            epoch_threshold=BRIDGE_EPOCH_THRESHOLD,",
        "            l_freq=BRIDGE_L_FREQ,",
        "            h_freq=BRIDGE_H_FREQ,",
        "            epoch_duration=BRIDGE_EPOCH_DURATION,",
        "            verbose=False,",
        "        )",
        "    )",
        "",
        "    return [",
        "        (",
        "            eeg_raw.ch_names[index_a],",
        "            eeg_raw.ch_names[index_b],",
        "        )",
        "        for index_a, index_b",
        "        in bridged_idx",
        "    ]",
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
        '        method="iir",',
        "        iir_params={",
        '            "order": FILTER_ORDER,',
        '            "ftype": "butter",',
        "        },",
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
        "        excluded = (",
        "            set(REFERENCE_EXCLUDE)",
        '            | set(raw.info["bads"])',
        "        )",
        "",
        "        reference_channels = [",
        "            channel",
        "            for channel in eeg_channels",
        "            if channel not in excluded",
        "        ]",
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
        '                f"Unknown pipeline step: {step_name}"',
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
        'raw.info["bads"] = list(BAD_CHANNELS)',
        "",
        "detected_bridge_pairs = detect_bridges(",
        "    raw",
        ")",
        "",
        "print(",
        '    "Detected bridge candidates:",',
        "    detected_bridge_pairs,",
        ")",
        "",
        "print(",
        '    "Researcher-confirmed bridges:",',
        "    CONFIRMED_BRIDGES,",
        ")",
        "",
        "# Confirmed bridge pairs are recorded here.",
        "# They are NOT automatically deleted or interpolated.",
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