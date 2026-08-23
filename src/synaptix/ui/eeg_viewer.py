import numpy as np
import pyqtgraph as pg

from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

from synaptix.core.recording import Recording


class EEGViewer(QWidget):
    WINDOW_SECONDS = 10.0
    MAX_VISIBLE_CHANNELS = 16

    def __init__(self):
        super().__init__()

        self.recording: Recording | None = None
        self.current_start = 0.0

        self.plot_widget = pg.PlotWidget()

        self.plot_widget.setLabel(
            "bottom",
            "Time",
            units="s",
        )

        self.plot_widget.showGrid(
            x=True,
            y=False,
            alpha=0.2,
        )

        layout = QVBoxLayout(self)
        layout.addWidget(
            self.plot_widget
        )

    def set_recording(
        self,
        recording: Recording,
    ):
        self.recording = recording
        self.current_start = 0.0

        self.render()

    def render(self):
        if self.recording is None:
            return

        self.plot_widget.clear()

        channels = self.recording.channels[
            :self.MAX_VISIBLE_CHANNELS
        ]

        data, times = self.recording.get_window(
            start_seconds=self.current_start,
            duration_seconds=self.WINDOW_SECONDS,
            channels=channels,
        )

        if data.size == 0:
            return

        # EEG volts → microvolts
        data_uv = data * 1_000_000

        amplitude = np.percentile(
            np.abs(data_uv),
            95,
        )

        spacing = max(
            amplitude * 3,
            50,
        )

        for index, channel in enumerate(
            channels
        ):
            offset = (
                len(channels) - index
            ) * spacing

            signal = (
                data_uv[index]
                + offset
            )

            self.plot_widget.plot(
                times,
                signal,
            )

        self.plot_widget.setXRange(
            self.current_start,
            self.current_start
            + self.WINDOW_SECONDS,
            padding=0,
        )