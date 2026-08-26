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

from synaptix.core.recording import (
    Recording,
)
from synaptix.models.artifact import (
    ArtifactCandidate,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
)
from synaptix.processing.pipeline import (
    EEGProcessingPipeline,
)
from synaptix.processing.step_registry import (
    definition_for,
)


class EEGViewer(QWidget):
    DEFAULT_WINDOW_SECONDS = 10.0
    MAX_INITIAL_CHANNELS = 16

    def __init__(
        self,
    ):
        super().__init__()

        # =====================================================
        # State
        # =====================================================

        self.recording: (
            Recording | None
        ) = None

        self.pipeline_config = (
            PipelineConfiguration.default()
        )

        self.current_start = 0.0

        self.window_seconds = (
            self.DEFAULT_WINDOW_SECONDS
        )

        self.amplitude_scale = 1.0

        self.artifact_candidates: list[
            ArtifactCandidate
        ] = []

        self.selected_candidate: (
            ArtifactCandidate | None
        ) = None

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus
        )

        self._build_ui()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(
        self,
    ):
        # =====================================================
        # Channels
        # =====================================================

        channel_title = QLabel(
            "Channels"
        )

        channel_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.channel_list = (
            QListWidget()
        )

        self.channel_list.setMaximumWidth(
            160
        )

        self.channel_list.itemChanged.connect(
            self._channels_changed
        )

        channel_layout = (
            QVBoxLayout()
        )

        channel_layout.addWidget(
            channel_title
        )

        channel_layout.addWidget(
            self.channel_list,
            stretch=1,
        )

        # =====================================================
        # RAW
        # =====================================================

        raw_title = QLabel(
            "RAW EEG"
        )

        raw_title.setStyleSheet(
            (
                "font-weight: 700;"
                "font-size: 13px;"
            )
        )

        raw_subtitle = QLabel(
            "Original recording • unchanged"
        )

        self.raw_plot = (
            pg.PlotWidget()
        )

        self._configure_plot(
            self.raw_plot
        )

        # =====================================================
        # PROCESSED
        # =====================================================

        processed_title = QLabel(
            "PROCESSED PREVIEW"
        )

        processed_title.setStyleSheet(
            (
                "font-weight: 700;"
                "font-size: 13px;"
            )
        )

        self.processed_description = (
            QLabel(
                "Band-pass Filter"
            )
        )

        self.processed_description.setWordWrap(
            True
        )

        self.processed_plot = (
            pg.PlotWidget()
        )

        self._configure_plot(
            self.processed_plot
        )

        self.processed_plot.setXLink(
            self.raw_plot
        )

        # =====================================================
        # Navigation
        # =====================================================

        self.previous_button = (
            QPushButton(
                "◀"
            )
        )

        self.previous_button.clicked.connect(
            self.previous_window
        )

        self.next_button = (
            QPushButton(
                "▶"
            )
        )

        self.next_button.clicked.connect(
            self.next_window
        )

        self.time_label = QLabel(
            "00:00 – 00:00"
        )

        self.time_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        self.time_slider.setRange(
            0,
            0,
        )

        self.time_slider.valueChanged.connect(
            self._slider_changed
        )

        self.window_selector = (
            QComboBox()
        )

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

        navigation_layout = (
            QHBoxLayout()
        )

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
            QLabel(
                "Window:"
            )
        )

        navigation_layout.addWidget(
            self.window_selector
        )

        amplitude_layout = (
            QHBoxLayout()
        )

        amplitude_layout.addWidget(
            self.amplitude_label
        )

        amplitude_layout.addWidget(
            self.amplitude_slider,
            stretch=1,
        )

        # =====================================================
        # Plots
        # =====================================================

        plot_layout = QVBoxLayout()

        plot_layout.addWidget(
            raw_title
        )

        plot_layout.addWidget(
            raw_subtitle
        )

        plot_layout.addWidget(
            self.raw_plot,
            stretch=1,
        )

        plot_layout.addWidget(
            processed_title
        )

        plot_layout.addWidget(
            self.processed_description
        )

        plot_layout.addWidget(
            self.processed_plot,
            stretch=1,
        )

        plot_layout.addLayout(
            navigation_layout
        )

        plot_layout.addLayout(
            amplitude_layout
        )

        # =====================================================
        # Root
        # =====================================================

        root = QHBoxLayout()

        root.addLayout(
            channel_layout
        )

        root.addLayout(
            plot_layout,
            stretch=1,
        )

        self.setLayout(
            root
        )

    # =========================================================
    # Plot config
    # =========================================================

    @staticmethod
    def _configure_plot(
        plot: pg.PlotWidget,
    ):
        plot.setBackground(
            "w"
        )

        plot.setLabel(
            "bottom",
            "Time",
            units="s",
        )

        plot.setLabel(
            "left",
            "Channels",
        )

        plot.showGrid(
            x=True,
            y=False,
            alpha=0.15,
        )

        plot.setMouseEnabled(
            x=True,
            y=False,
        )

    # =========================================================
    # Recording
    # =========================================================

    def set_recording(
        self,
        recording: Recording,
    ):
        self.recording = recording

        self.current_start = 0.0

        self._populate_channels()

        self._configure_time_slider()

        self.render()

    # =========================================================
    # Pipeline
    # =========================================================

    def set_pipeline_config(
        self,
        configuration: PipelineConfiguration,
    ):
        self.pipeline_config = (
            configuration
        )

        enabled_names = [
            definition_for(
                step.step_type
            ).display_name
            for step
            in configuration.steps
            if step.enabled
        ]

        if enabled_names:
            self.processed_description.setText(
                " → ".join(
                    enabled_names
                )
            )

        else:
            self.processed_description.setText(
                "No processing steps enabled"
            )

        self.render()

    # =========================================================
    # Channels
    # =========================================================

    def _populate_channels(
        self,
    ):
        if self.recording is None:
            return

        self.channel_list.blockSignals(
            True
        )

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

            item.setCheckState(
                (
                    Qt.CheckState.Checked
                    if index
                    < self.MAX_INITIAL_CHANNELS
                    else Qt.CheckState.Unchecked
                )
            )

            self.channel_list.addItem(
                item
            )

        self.channel_list.blockSignals(
            False
        )

    def selected_channels(
        self,
    ) -> list[str]:
        channels: list[str] = []

        for index in range(
            self.channel_list.count()
        ):
            item = (
                self.channel_list.item(
                    index
                )
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

    # =========================================================
    # Candidates
    # =========================================================

    def set_artifact_candidates(
        self,
        candidates: list[
            ArtifactCandidate
        ],
    ):
        self.artifact_candidates = (
            candidates
        )

        self.selected_candidate = None

        self.render()

    def go_to_candidate(
        self,
        candidate: ArtifactCandidate,
    ):
        self.selected_candidate = (
            candidate
        )

        midpoint = (
            candidate.start_seconds
            + candidate.end_seconds
        ) / 2

        self.set_start_time(
            midpoint
            - self.window_seconds / 2
        )

    # =========================================================
    # Navigation
    # =========================================================

    def previous_window(
        self,
    ):
        self.set_start_time(
            self.current_start
            - self.window_seconds
        )

    def next_window(
        self,
    ):
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

        maximum = max(
            0.0,
            (
                self.recording.duration_seconds
                - self.window_seconds
            ),
        )

        self.current_start = min(
            max(
                0.0,
                seconds,
            ),
            maximum,
        )

        self.time_slider.blockSignals(
            True
        )

        self.time_slider.setValue(
            int(
                self.current_start
                * 10
            )
        )

        self.time_slider.blockSignals(
            False
        )

        self.render()

    def _configure_time_slider(
        self,
    ):
        if self.recording is None:
            return

        maximum = max(
            0.0,
            (
                self.recording.duration_seconds
                - self.window_seconds
            ),
        )

        self.time_slider.setRange(
            0,
            int(
                maximum
                * 10
            ),
        )

    def _slider_changed(
        self,
        value: int,
    ):
        self.current_start = (
            value / 10
        )

        self.render()

    def _window_size_changed(
        self,
        text: str,
    ):
        self.window_seconds = float(
            text.split()[0]
        )

        self._configure_time_slider()

        self.set_start_time(
            self.current_start
        )

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

    # =========================================================
    # Render
    # =========================================================

    def render(
        self,
    ):
        if self.recording is None:
            return

        channels = (
            self.selected_channels()
        )

        self.raw_plot.clear()
        self.processed_plot.clear()

        if not channels:
            return

        try:
            pipeline = (
                EEGProcessingPipeline(
                    configuration=(
                        self.pipeline_config
                    )
                )
            )

            result = (
                pipeline.process_window(
                    recording=self.recording,
                    start_seconds=(
                        self.current_start
                    ),
                    duration_seconds=(
                        self.window_seconds
                    ),
                    channels=channels,
                )
            )

        except Exception as error:
            self.processed_description.setText(
                (
                    "Processing error: "
                    f"{error}"
                )
            )

            return

        if result.raw_data.size == 0:
            return

        raw_uv = (
            result.raw_data
            * 1_000_000
        )

        processed_uv = (
            result.processed_data
            * 1_000_000
        )

        robust_amplitude = float(
            np.percentile(
                np.abs(
                    raw_uv
                ),
                95,
            )
        )

        spacing = max(
            robust_amplitude
            * 3,
            50.0,
        )

        channel_count = len(
            channels
        )

        ticks = []

        for index, channel in enumerate(
            channels
        ):
            offset = (
                channel_count
                - index
                - 1
            ) * spacing

            self.raw_plot.plot(
                result.times,
                (
                    raw_uv[index]
                    * self.amplitude_scale
                    + offset
                ),
                pen=pg.mkPen(
                    50,
                    50,
                    50,
                    width=1,
                ),
            )

            self.processed_plot.plot(
                result.times,
                (
                    processed_uv[index]
                    * self.amplitude_scale
                    + offset
                ),
                pen=pg.mkPen(
                    40,
                    95,
                    170,
                    width=1,
                ),
            )

            ticks.append(
                (
                    offset,
                    channel,
                )
            )

        self.raw_plot.getAxis(
            "left"
        ).setTicks(
            [
                ticks
            ]
        )

        self.processed_plot.getAxis(
            "left"
        ).setTicks(
            [
                ticks
            ]
        )

        self._draw_artifact_regions(
            self.raw_plot
        )

        self._draw_artifact_regions(
            self.processed_plot
        )

        start = (
            self.current_start
        )

        end = min(
            (
                start
                + self.window_seconds
            ),
            self.recording.duration_seconds,
        )

        for plot in [
            self.raw_plot,
            self.processed_plot,
        ]:
            plot.setXRange(
                start,
                end,
                padding=0,
            )

            plot.setYRange(
                -spacing,
                (
                    channel_count
                    * spacing
                ),
                padding=0.02,
            )

        self.time_label.setText(
            (
                f"{self._format_time(start)}"
                " – "
                f"{self._format_time(end)}"
                " / "
                f"{self._format_time(self.recording.duration_seconds)}"
            )
        )

    # =========================================================
    # Artifact regions
    # =========================================================

    def _draw_artifact_regions(
        self,
        plot: pg.PlotWidget,
    ):
        window_end = (
            self.current_start
            + self.window_seconds
        )

        for candidate in (
            self.artifact_candidates
        ):
            if (
                candidate.end_seconds
                < self.current_start
                or candidate.start_seconds
                > window_end
            ):
                continue

            if (
                candidate
                is self.selected_candidate
            ):
                brush = pg.mkBrush(
                    255,
                    170,
                    40,
                    70,
                )

            elif (
                candidate.accepted
                is True
            ):
                brush = pg.mkBrush(
                    60,
                    180,
                    100,
                    40,
                )

            elif (
                candidate.accepted
                is False
            ):
                brush = pg.mkBrush(
                    130,
                    130,
                    130,
                    25,
                )

            else:
                brush = pg.mkBrush(
                    230,
                    70,
                    70,
                    40,
                )

            region = (
                pg.LinearRegionItem(
                    values=(
                        candidate.start_seconds,
                        candidate.end_seconds,
                    ),
                    movable=False,
                    brush=brush,
                )
            )

            region.setZValue(
                -10
            )

            plot.addItem(
                region
            )

    # =========================================================
    # Keyboard
    # =========================================================

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

    # =========================================================
    # Time
    # =========================================================

    @staticmethod
    def _format_time(
        seconds: float,
    ) -> str:
        seconds = max(
            0,
            int(seconds),
        )

        hours = (
            seconds // 3600
        )

        minutes = (
            seconds % 3600
        ) // 60

        remaining = (
            seconds % 60
        )

        if hours:
            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{remaining:02d}"
            )

        return (
            f"{minutes:02d}:"
            f"{remaining:02d}"
        )