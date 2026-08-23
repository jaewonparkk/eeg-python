from pathlib import Path

import mne
from mne.io import BaseRaw


SUPPORTED_EXTENSIONS = {
    ".edf",
    ".bdf",
    ".fif",
    ".set",
}


def load_raw(filepath: str | Path) -> BaseRaw:
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(
            f"EEG file not found: {path}"
        )

    suffix = path.suffix.lower()

    if suffix == ".edf":
        return mne.io.read_raw_edf(
            path,
            preload=False,
            verbose=False,
        )

    if suffix == ".bdf":
        return mne.io.read_raw_bdf(
            path,
            preload=False,
            verbose=False,
        )

    if suffix == ".fif":
        return mne.io.read_raw_fif(
            path,
            preload=False,
            verbose=False,
        )

    if suffix == ".set":
        return mne.io.read_raw_eeglab(
            path,
            preload=False,
            verbose=False,
        )

    raise ValueError(
        f"Unsupported EEG format: {suffix}"
    )