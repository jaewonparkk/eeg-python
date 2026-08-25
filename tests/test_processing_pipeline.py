from pathlib import Path

import mne
import numpy as np

from synaptix.core.recording import (
    Recording,
)
from synaptix.models.processing import (
    ProcessingSettings,
)
from synaptix.processing.pipeline import (
    EEGProcessingPipeline,
)


def create_synthetic_recording() -> Recording:
    sampling_frequency = 500.0

    duration_seconds = 10.0

    times = np.arange(
        0,
        duration_seconds,
        1.0 / sampling_frequency,
    )

    # 10 Hz EEG-like signal
    signal_10hz = (
        20e-6
        * np.sin(
            2
            * np.pi
            * 10
            * times
        )
    )

    # 60 Hz contamination
    signal_60hz = (
        15e-6
        * np.sin(
            2
            * np.pi
            * 60
            * times
        )
    )

    signal = (
        signal_10hz
        + signal_60hz
    )

    data = signal[
        np.newaxis,
        :
    ]

    info = mne.create_info(
        ch_names=[
            "Fp1"
        ],
        sfreq=(
            sampling_frequency
        ),
        ch_types=[
            "eeg"
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


def spectral_amplitude(
    signal: np.ndarray,
    sampling_frequency: float,
    target_frequency: float,
) -> float:
    frequencies = np.fft.rfftfreq(
        len(signal),
        d=(
            1.0
            / sampling_frequency
        ),
    )

    spectrum = np.abs(
        np.fft.rfft(
            signal
        )
    )

    index = int(
        np.argmin(
            np.abs(
                frequencies
                - target_frequency
            )
        )
    )

    return float(
        spectrum[
            index
        ]
    )


def test_processing_preserves_shape():
    recording = (
        create_synthetic_recording()
    )

    settings = (
        ProcessingSettings(
            bandpass_enabled=True,
            highpass_hz=0.5,
            lowpass_hz=45.0,
            notch_enabled=False,
        )
    )

    pipeline = (
        EEGProcessingPipeline(
            settings
        )
    )

    result = (
        pipeline.process_window(
            recording=recording,
            start_seconds=2.0,
            duration_seconds=5.0,
            channels=[
                "Fp1"
            ],
        )
    )

    assert (
        result.raw_data.shape
        == result.processed_data.shape
    )

    assert (
        result.raw_data.shape[0]
        == 1
    )

    assert (
        len(result.times)
        == result.raw_data.shape[1]
    )


def test_lowpass_reduces_60hz_energy():
    recording = (
        create_synthetic_recording()
    )

    settings = (
        ProcessingSettings(
            bandpass_enabled=True,
            highpass_hz=0.5,
            lowpass_hz=45.0,
            notch_enabled=False,
        )
    )

    pipeline = (
        EEGProcessingPipeline(
            settings
        )
    )

    result = (
        pipeline.process_window(
            recording=recording,
            start_seconds=2.0,
            duration_seconds=5.0,
            channels=[
                "Fp1"
            ],
        )
    )

    raw_60hz = spectral_amplitude(
        result.raw_data[0],
        recording.sampling_frequency,
        60.0,
    )

    processed_60hz = spectral_amplitude(
        result.processed_data[0],
        recording.sampling_frequency,
        60.0,
    )

    assert (
        processed_60hz
        < raw_60hz
        * 0.1
    )