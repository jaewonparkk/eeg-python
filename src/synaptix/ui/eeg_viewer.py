import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from synaptix.core.recording import Recording


class EEGViewer(QWidget):
    DEFAULT_WINDOW_SECONDS = 10.0
    MAX_INITIAL_CHANNELS = 16

    def __init__(self):
        super().__init__()

        self.recording: Recording | None = None

        self.current_start = 0.0
        self.window_seconds = self.DEFAULT_WINDOW_SECONDS
        self.amplitude_scale = 1.0

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):
        # ---------- Plot ----------
        self.plot_widget = pg.PlotWidget()

        self.plot_widget.setLabel(
            "bottom",
            "Time",
            units="s",
        )

        self.plot_widget.setLabel(
            "left",
            "Channels",
        )

        self.plot_widget.showGrid(
            x=True,
            y=False,
            alpha=0.15,
        )

        # Prevent users from accidentally panning vertically
        self.plot_widget.setMouseEnabled(
            x=True,
            y=False,
        )

        # ---------- Navigation ----------
        self.previous_button = QPushButton("◀")
        self.previous_button.clicked.connect(
            self.previous_window
        )

        self.next_button = QPushButton("▶")
        self.next_button.clicked.connect(
            self.next_window
        )

        self.time_label = QLabel("0.0 – 0.0 s")

        self.time_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        self.time_slider.setRange(0, 0)

        self.time_slider.valueChanged.connect(
            self._slider_changed
        )

        # ---------- Window size ----------
        self.window_selector = QComboBox()

        self.window_selector.addItems(
            [
                "5 sec",
                "10 sec",
                "20 sec",
                "30 sec",
            ]
        )

        self.window_selector.setCurrentText(
            "10 sec"
        )

        self.window_selector.currentTextChanged.connect(
            self._window_size_changed
        )

        # ---------- Amplitude ----------
        self.amplitude_label = QLabel(
            "Amplitude: 100%"
        )

        self.amplitude_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        self.amplitude_slider.setRange(
            25,
            400,
        )

        self.amplitude_slider.setValue(
            100
        )

        self.amplitude_slider.valueChanged.connect(
            self._amplitude_changed
        )

        # ---------- Channel selector ----------
        self.channel_list = QListWidget()

        self.channel_list.setMaximumWidth(
            180
        )

        self.channel_list.itemChanged.connect(
            self._channels_changed
        )

        channel_title = QLabel(
            "Channels"
        )

        # ---------- Control layout ----------
        navigation_layout = QHBoxLayout()

        navigation_layout.addWidget(
            self.previous_button
        )

        navigation_layout.addWidget(
            self.next_button
        )

        navigation_layout.addWidget(
            self.time_label
        )

        navigation_layout.addWidget(
            self.time_slider,
            stretch=1,
        )

        navigation_layout.addWidget(
            QLabel("Window:")
        )

        navigation_layout.addWidget(
            self.window_selector
        )

        amplitude_layout = QHBoxLayout()

        amplitude_layout.addWidget(
            self.amplitude_label
        )

        amplitude_layout.addWidget(
            self.amplitude_slider
        )

        # ---------- Main content ----------
        plot_layout = QVBoxLayout()

        plot_layout.addWidget(
            self.plot_widget,
            stretch=1,
        )

        plot_layout.addLayout(
            navigation_layout
        )

        plot_layout.addLayout(
            amplitude_layout
        )

        channel_layout = QVBoxLayout()

        channel_layout.addWidget(
            channel_title
        )

        channel_layout.addWidget(
            self.channel_list
        )

        content_layout = QHBoxLayout()

        content_layout.addLayout(
            channel_layout
        )

        content_layout.addLayout(
            plot_layout,
            stretch=1,
        )

        self.setLayout(
            content_layout
        )

    # ---------------------------------------------------------
    # Recording
    # ---------------------------------------------------------

    def set_recording(
        self,
        recording: Recording,
    ):
        self.recording = recording

        self.current_start = 0.0

        self._populate_channels()
        self._configure_time_slider()

        self.render()

    def _populate_channels(self):
        if self.recording is None:
            return

        self.channel_list.blockSignals(True)

        self.channel_list.clear()

        for index, channel in enumerate(
            self.recording.channels
        ):
            item = QListWidgetItem(
                channel
            )

            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
            )

            if index < self.MAX_INITIAL_CHANNELS:
                item.setCheckState(
                    Qt.CheckState.Checked
                )
            else:
                item.setCheckState(
                    Qt.CheckState.Unchecked
                )

            self.channel_list.addItem(
                item
            )

        self.channel_list.blockSignals(False)

    # ---------------------------------------------------------
    # Channel selection
    # ---------------------------------------------------------

    def selected_channels(
        self,
    ) -> list[str]:
        channels = []

        for index in range(
            self.channel_list.count()
        ):
            item = self.channel_list.item(
                index
            )

            if (
                item.checkState()
                == Qt.CheckState.Checked
            ):
                channels.append(
                    item.text()
                )

        return channels

    def _channels_changed(
        self,
        _item,
    ):
        self.render()

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    def previous_window(self):
        if self.recording is None:
            return

        self.set_start_time(
            self.current_start
            - self.window_seconds
        )

    def next_window(self):
        if self.recording is None:
            return

        self.set_start_time(
            self.current_start
            + self.window_seconds
        )

    def set_start_time(
        self,
        seconds: float,
    ):
        if self.recording is None:
            return

        max_start = max(
            0.0,
            self.recording.duration_seconds
            - self.window_seconds,
        )

        self.current_start = min(
            max(seconds, 0.0),
            max_start,
        )

        slider_value = int(
            self.current_start * 10
        )

        self.time_slider.blockSignals(True)

        self.time_slider.setValue(
            slider_value
        )

        self.time_slider.blockSignals(False)

        self.render()

    def _configure_time_slider(self):
        if self.recording is None:
            return

        max_start = max(
            0.0,
            self.recording.duration_seconds
            - self.window_seconds,
        )

        # Slider resolution = 0.1 seconds
        self.time_slider.setRange(
            0,
            int(max_start * 10),
        )

    def _slider_changed(
        self,
        value: int,
    ):
        self.current_start = (
            value / 10
        )

        self.render()

    # ---------------------------------------------------------
    # Window size
    # ---------------------------------------------------------

    def _window_size_changed(
        self,
        text: str,
    ):
        value = text.split()[0]

        self.window_seconds = float(
            value
        )

        self._configure_time_slider()

        self.set_start_time(
            self.current_start
        )

    # ---------------------------------------------------------
    # Amplitude
    # ---------------------------------------------------------

    def _amplitude_changed(
        self,
        value: int,
    ):
        self.amplitude_scale = (
            value / 100.0
        )

        self.amplitude_label.setText(
            f"Amplitude: {value}%"
        )

        self.render()

    # ---------------------------------------------------------
    # Rendering
    # ---------------------------------------------------------

    def render(self):
        if self.recording is None:
            return

        channels = self.selected_channels()

        self.plot_widget.clear()

        if not channels:
            self.time_label.setText(
                "No channels selected"
            )
            return

        data, times = (
            self.recording.get_window(
                start_seconds=self.current_start,
                duration_seconds=self.window_seconds,
                channels=channels,
            )
        )

        if data.size == 0:
            return

        # EEG volts -> microvolts
        data_uv = data * 1_000_000

        # Robust amplitude estimate.
        # Avoids one giant artifact determining
        # all of the vertical spacing.
        robust_amplitude = float(
            np.percentile(
                np.abs(data_uv),
                95,
            )
        )

        spacing = max(
            robust_amplitude * 3,
            50.0,
        )

        axis_ticks = []

        channel_count = len(
            channels
        )

        for index, channel in enumerate(
            channels
        ):
            # First channel should appear at top
            offset = (
                channel_count
                - index
                - 1
            ) * spacing

            signal = (
                data_uv[index]
                * self.amplitude_scale
                + offset
            )

            self.plot_widget.plot(
                times,
                signal,
            )

            axis_ticks.append(
                (
                    offset,
                    channel,
                )
            )

        # Channel names on Y axis
        left_axis = (
            self.plot_widget.getAxis(
                "left"
            )
        )

        left_axis.setTicks(
            [axis_ticks]
        )

        start = self.current_start

        end = min(
            start + self.window_seconds,
            self.recording.duration_seconds,
        )

        self.plot_widget.setXRange(
            start,
            end,
            padding=0,
        )

        self.plot_widget.setYRange(
            -spacing,
            channel_count * spacing,
            padding=0.02,
        )

        self.time_label.setText(
            f"{self._format_time(start)}"
            f" – "
            f"{self._format_time(end)}"
            f" / "
            f"{self._format_time(self.recording.duration_seconds)}"
        )

    # ---------------------------------------------------------
    # Keyboard
    # ---------------------------------------------------------

    def keyPressEvent(
        self,
        event,
    ):
        if (
            event.key()
            == Qt.Key.Key_Left
        ):
            self.previous_window()
            return

        if (
            event.key()
            == Qt.Key.Key_Right
        ):
            self.next_window()
            return

        super().keyPressEvent(
            event
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _format_time(
        seconds: float,
    ) -> str:
        seconds = max(
            0,
            int(seconds),
        )

        minutes = (
            seconds // 60
        )

        remaining_seconds = (
            seconds % 60
        )

        return (
            f"{minutes:02d}:"
            f"{remaining_seconds:02d}"
        )