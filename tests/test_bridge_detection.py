from pathlib import Path

import mne
import numpy as np

from synaptix.analysis.bridge_detection import (
    ElectrodeBridgeAnalyzer,
)
from synaptix.core.recording import (
    Recording,
)
from synaptix.models.bridge import (
    BridgeDetectionSettings,
)


def create_bridge_recording() -> Recording:
    sfreq = 250.0

    times = np.arange(
        0,
        10,
        1 / sfreq,
    )

    signal = (
        20e-6
        * np.sin(
            2
            * np.pi
            * 10
            * times
        )
    )

    data = np.vstack(
        [
            signal,
            signal
            + 0.1e-6
            * np.sin(
                2
                * np.pi
                * 3
                * times
            ),
            (
                25e-6
                * np.sin(
                    2
                    * np.pi
                    * 7
                    * times
                )
            ),
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
            "bridge_test.fif"
        ),
    )


def test_bridge_analyzer_maps_indices_to_channels(
    monkeypatch,
):
    recording = (
        create_bridge_recording()
    )

    def fake_compute(
        raw,
        **_kwargs,
    ):
        ed_matrix = np.full(
            (
                4,
                3,
                3,
            ),
            np.nan,
        )

        ed_matrix[
            :,
            0,
            1,
        ] = [
            1.0,
            2.0,
            3.0,
            2.0,
        ]

        return (
            [
                (
                    0,
                    1,
                )
            ],
            ed_matrix,
        )

    monkeypatch.setattr(
        mne.preprocessing,
        "compute_bridged_electrodes",
        fake_compute,
    )

    analyzer = (
        ElectrodeBridgeAnalyzer(
            BridgeDetectionSettings()
        )
    )

    results = (
        analyzer.analyze_recording(
            recording
        )
    )

    assert len(
        results
    ) == 1

    candidate = results[
        0
    ]

    assert (
        candidate.channel_a
        == "Fp1"
    )

    assert (
        candidate.channel_b
        == "Fp2"
    )

    assert (
        candidate.median_electrical_distance_uv2
        == 2.0
    )


def test_confirm_and_clear_bridge_pair():
    recording = (
        create_bridge_recording()
    )

    recording.confirm_bridge_pair(
        "Fp1",
        "Fp2",
    )

    assert (
        (
            "Fp1",
            "Fp2",
        )
        in recording.confirmed_bridge_pairs
    )

    recording.clear_bridge_pair(
        "Fp1",
        "Fp2",
    )

    assert (
        recording.confirmed_bridge_pairs
        == []
    )


def test_bridge_pair_is_normalized():
    recording = (
        create_bridge_recording()
    )

    recording.confirm_bridge_pair(
        "Fp2",
        "Fp1",
    )

    assert (
        recording.confirmed_bridge_pairs
        == [
            (
                "Fp1",
                "Fp2",
            )
        ]
    )