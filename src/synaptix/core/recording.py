from pathlib import Path

import numpy as np
from mne.io import BaseRaw

from synaptix.io.loaders import (
    load_raw,
)


class Recording:
    def __init__(
        self,
        raw: BaseRaw,
        source_path: Path,
    ):
        self._raw = raw

        self.source_path = (
            source_path
        )

    # =========================================================
    # Construction
    # =========================================================

    @classmethod
    def from_file(
        cls,
        filepath: str | Path,
    ) -> "Recording":
        path = Path(
            filepath
        )

        raw = load_raw(
            path
        )

        return cls(
            raw=raw,
            source_path=path,
        )

    # =========================================================
    # Metadata
    # =========================================================

    @property
    def name(
        self,
    ) -> str:
        return self.source_path.name

    @property
    def channels(
        self,
    ) -> list[str]:
        return list(
            self._raw.ch_names
        )

    @property
    def channel_types(
        self,
    ) -> dict[str, str]:
        types = (
            self._raw.get_channel_types()
        )

        return dict(
            zip(
                self.channels,
                types,
            )
        )

    @property
    def eeg_channels(
        self,
    ) -> list[str]:
        return [
            channel
            for channel, channel_type
            in self.channel_types.items()
            if channel_type == "eeg"
        ]

    @property
    def channel_count(
        self,
    ) -> int:
        return len(
            self.channels
        )

    @property
    def eeg_channel_count(
        self,
    ) -> int:
        return len(
            self.eeg_channels
        )

    @property
    def sampling_frequency(
        self,
    ) -> float:
        return float(
            self._raw.info[
                "sfreq"
            ]
        )

    @property
    def duration_seconds(
        self,
    ) -> float:
        return (
            self._raw.n_times
            / self.sampling_frequency
        )

    # =========================================================
    # Bad channels
    # =========================================================

    @property
    def bad_channels(
        self,
    ) -> list[str]:
        return list(
            self._raw.info[
                "bads"
            ]
        )

    def mark_bad_channel(
        self,
        channel: str,
    ):
        if channel not in self.channels:
            raise ValueError(
                (
                    "Unknown channel: "
                    f"{channel}"
                )
            )

        bads = list(
            self._raw.info[
                "bads"
            ]
        )

        if channel not in bads:
            bads.append(
                channel
            )

        self._raw.info[
            "bads"
        ] = bads

    def mark_good_channel(
        self,
        channel: str,
    ):
        if channel not in self.channels:
            raise ValueError(
                (
                    "Unknown channel: "
                    f"{channel}"
                )
            )

        bads = [
            bad
            for bad
            in self._raw.info[
                "bads"
            ]
            if bad != channel
        ]

        self._raw.info[
            "bads"
        ] = bads

    def set_bad_channels(
        self,
        channels: list[str],
    ):
        unknown = [
            channel
            for channel in channels
            if channel
            not in self.channels
        ]

        if unknown:
            raise ValueError(
                (
                    "Unknown bad channels: "
                    + ", ".join(
                        unknown
                    )
                )
            )

        ordered = [
            channel
            for channel
            in self.channels
            if channel in channels
        ]

        self._raw.info[
            "bads"
        ] = ordered

    # =========================================================
    # Window access
    # =========================================================

    def get_window(
        self,
        start_seconds: float,
        duration_seconds: float,
        channels: list[str] | None = None,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
    ]:
        start_sample = int(
            start_seconds
            * self.sampling_frequency
        )

        stop_sample = int(
            (
                start_seconds
                + duration_seconds
            )
            * self.sampling_frequency
        )

        start_sample = max(
            0,
            start_sample,
        )

        stop_sample = min(
            self._raw.n_times,
            stop_sample,
        )

        if channels:
            picks = [
                self._raw.ch_names.index(
                    channel
                )
                for channel
                in channels
            ]

        else:
            picks = list(
                range(
                    self.channel_count
                )
            )

        data, times = (
            self._raw[
                picks,
                start_sample:stop_sample,
            ]
        )

        return (
            data,
            times,
        )