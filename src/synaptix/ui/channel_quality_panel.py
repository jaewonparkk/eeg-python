from PySide6.QtCore import (
    Signal,
)

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from synaptix.models.channel_quality import (
    ChannelQualityResult,
    ChannelQualityThresholds,
)


class ChannelQualityPanel(QWidget):
    analyze_requested = Signal(
        object
    )

    mark_bad_requested = Signal(
        str
    )

    keep_requested = Signal(
        str
    )

    def __init__(
        self,
    ):
        super().__init__()

        self.results: list[
            ChannelQualityResult
        ] = []

        self.bad_channels: set[
            str
        ] = set()

        self.current_result: (
            ChannelQualityResult
            | None
        ) = None

        # =====================================================
        # Title
        # =====================================================

        title = QLabel(
            "Channel Quality"
        )

        title.setStyleSheet(
            (
                "font-size: 18px;"
                "font-weight: 600;"
            )
        )

        subtitle = QLabel(
            (
                "Surface channels that may require "
                "human review. These metrics are "
                "heuristic, not definitive diagnoses."
            )
        )

        subtitle.setWordWrap(
            True
        )

        # =====================================================
        # Threshold controls
        # =====================================================

        threshold_title = QLabel(
            "Review Thresholds"
        )

        threshold_title.setStyleSheet(
            "font-weight: 600;"
        )

        threshold_form = (
            QFormLayout()
        )

        self.extreme_amplitude_input = (
            QDoubleSpinBox()
        )

        self.extreme_amplitude_input.setRange(
            10.0,
            2000.0,
        )

        self.extreme_amplitude_input.setValue(
            150.0
        )

        self.extreme_amplitude_input.setSuffix(
            " µV"
        )

        self.extreme_fraction_input = (
            QDoubleSpinBox()
        )

        self.extreme_fraction_input.setRange(
            0.0,
            100.0,
        )

        self.extreme_fraction_input.setDecimals(
            2
        )

        self.extreme_fraction_input.setValue(
            1.0
        )

        self.extreme_fraction_input.setSuffix(
            " %"
        )

        self.flat_delta_input = (
            QDoubleSpinBox()
        )

        self.flat_delta_input.setRange(
            0.01,
            50.0,
        )

        self.flat_delta_input.setDecimals(
            2
        )

        self.flat_delta_input.setValue(
            0.5
        )

        self.flat_delta_input.setSuffix(
            " µV"
        )

        self.flat_fraction_input = (
            QDoubleSpinBox()
        )

        self.flat_fraction_input.setRange(
            0.0,
            100.0,
        )

        self.flat_fraction_input.setDecimals(
            1
        )

        self.flat_fraction_input.setValue(
            10.0
        )

        self.flat_fraction_input.setSuffix(
            " %"
        )

        self.high_std_ratio_input = (
            QDoubleSpinBox()
        )

        self.high_std_ratio_input.setRange(
            1.1,
            100.0,
        )

        self.high_std_ratio_input.setValue(
            4.0
        )

        self.high_std_ratio_input.setSuffix(
            " ×"
        )

        self.low_std_ratio_input = (
            QDoubleSpinBox()
        )

        self.low_std_ratio_input.setRange(
            0.01,
            0.99,
        )

        self.low_std_ratio_input.setDecimals(
            2
        )

        self.low_std_ratio_input.setValue(
            0.25
        )

        self.min_correlation_input = (
            QDoubleSpinBox()
        )

        self.min_correlation_input.setRange(
            -1.0,
            1.0,
        )

        self.min_correlation_input.setDecimals(
            2
        )

        self.min_correlation_input.setValue(
            0.10
        )

        threshold_form.addRow(
            "Extreme amplitude",
            self.extreme_amplitude_input,
        )

        threshold_form.addRow(
            "Extreme samples",
            self.extreme_fraction_input,
        )

        threshold_form.addRow(
            "Flat change ≤",
            self.flat_delta_input,
        )

        threshold_form.addRow(
            "Flat fraction",
            self.flat_fraction_input,
        )

        threshold_form.addRow(
            "High std ratio",
            self.high_std_ratio_input,
        )

        threshold_form.addRow(
            "Low std ratio",
            self.low_std_ratio_input,
        )

        threshold_form.addRow(
            "Min correlation",
            self.min_correlation_input,
        )

        # =====================================================
        # Analyze
        # =====================================================

        self.analyze_button = QPushButton(
            "Analyze Channel Quality"
        )

        self.analyze_button.clicked.connect(
            self._analyze_clicked
        )

        self.progress_bar = (
            QProgressBar()
        )

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        self.status_label = QLabel(
            "No channel analysis yet."
        )

        self.status_label.setWordWrap(
            True
        )

        # =====================================================
        # Channel list
        # =====================================================

        result_title = QLabel(
            "Channels"
        )

        result_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.list_widget = (
            QListWidget()
        )

        self.list_widget.currentRowChanged.connect(
            self._row_changed
        )

        # =====================================================
        # Details
        # =====================================================

        detail_title = QLabel(
            "Channel Details"
        )

        detail_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.channel_label = QLabel(
            "Channel: —"
        )

        self.state_label = QLabel(
            "State: —"
        )

        self.std_label = QLabel(
            "Std deviation: —"
        )

        self.std_ratio_label = QLabel(
            "Std ratio: —"
        )

        self.range_label = QLabel(
            "Peak-to-peak: —"
        )

        self.extreme_label = QLabel(
            "Extreme samples: —"
        )

        self.flat_label = QLabel(
            "Near-flat samples: —"
        )

        self.correlation_label = QLabel(
            "Median correlation: —"
        )

        why_title = QLabel(
            "Why was this flagged?"
        )

        why_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.reason_label = QLabel(
            "Select a channel."
        )

        self.reason_label.setWordWrap(
            True
        )

        # =====================================================
        # Decisions
        # =====================================================

        self.keep_button = QPushButton(
            "Keep / Mark Good"
        )

        self.bad_button = QPushButton(
            "Mark Bad Channel"
        )

        self.keep_button.clicked.connect(
            self._keep_clicked
        )

        self.bad_button.clicked.connect(
            self._bad_clicked
        )

        self.keep_button.setEnabled(
            False
        )

        self.bad_button.setEnabled(
            False
        )

        # =====================================================
        # Layout
        # =====================================================

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            threshold_title
        )

        layout.addLayout(
            threshold_form
        )

        layout.addWidget(
            self.analyze_button
        )

        layout.addWidget(
            self.progress_bar
        )

        layout.addWidget(
            self.status_label
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            result_title
        )

        layout.addWidget(
            self.list_widget,
            stretch=1,
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            detail_title
        )

        layout.addWidget(
            self.channel_label
        )

        layout.addWidget(
            self.state_label
        )

        layout.addWidget(
            self.std_label
        )

        layout.addWidget(
            self.std_ratio_label
        )

        layout.addWidget(
            self.range_label
        )

        layout.addWidget(
            self.extreme_label
        )

        layout.addWidget(
            self.flat_label
        )

        layout.addWidget(
            self.correlation_label
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            why_title
        )

        layout.addWidget(
            self.reason_label
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            self.keep_button
        )

        layout.addWidget(
            self.bad_button
        )

    # =========================================================
    # Thresholds
    # =========================================================

    def current_thresholds(
        self,
    ) -> ChannelQualityThresholds:
        return ChannelQualityThresholds(
            extreme_amplitude_uv=(
                self.extreme_amplitude_input
                .value()
            ),
            extreme_fraction=(
                self.extreme_fraction_input
                .value()
                / 100.0
            ),
            flat_delta_uv=(
                self.flat_delta_input
                .value()
            ),
            flat_fraction=(
                self.flat_fraction_input
                .value()
                / 100.0
            ),
            high_std_ratio=(
                self.high_std_ratio_input
                .value()
            ),
            low_std_ratio=(
                self.low_std_ratio_input
                .value()
            ),
            min_median_correlation=(
                self.min_correlation_input
                .value()
            ),
        )

    def _analyze_clicked(
        self,
    ):
        self.analyze_requested.emit(
            self.current_thresholds()
        )

    # =========================================================
    # Results
    # =========================================================

    def set_results(
        self,
        results: list[
            ChannelQualityResult
        ],
    ):
        self.results = results

        flagged = sum(
            result.flagged
            for result in results
        )

        self.status_label.setText(
            (
                f"{flagged} of "
                f"{len(results)} channels "
                "flagged for review."
            )
        )

        self.progress_bar.setValue(
            100
        )

        self.set_running(
            False
        )

        self._populate_list()

    def clear_results(
        self,
    ):
        self.results = []

        self.current_result = None

        self.list_widget.clear()

        self.progress_bar.setValue(
            0
        )

        self.status_label.setText(
            "No channel analysis yet."
        )

        self._clear_details()

    # =========================================================
    # Bad state
    # =========================================================

    def refresh_bad_states(
        self,
        bad_channels: list[str],
    ):
        self.bad_channels = set(
            bad_channels
        )

        if self.results:
            selected_channel = (
                self.current_result.channel
                if self.current_result
                is not None
                else None
            )

            self._populate_list(
                selected_channel=(
                    selected_channel
                )
            )

    # =========================================================
    # List
    # =========================================================

    def _populate_list(
        self,
        selected_channel: str | None = None,
    ):
        self.list_widget.blockSignals(
            True
        )

        self.list_widget.clear()

        selected_row = 0

        for index, result in enumerate(
            self.results
        ):
            self.list_widget.addItem(
                self._item_text(
                    result
                )
            )

            if (
                selected_channel
                == result.channel
            ):
                selected_row = index

        if self.results:
            self.list_widget.setCurrentRow(
                selected_row
            )

        self.list_widget.blockSignals(
            False
        )

        if self.results:
            self._show_result(
                selected_row
            )

    def _item_text(
        self,
        result: ChannelQualityResult,
    ) -> str:
        if (
            result.channel
            in self.bad_channels
        ):
            return (
                f"● {result.channel} "
                "• MARKED BAD"
            )

        if result.flagged:
            return (
                f"⚠ {result.channel} "
                "• REVIEW"
            )

        return (
            f"✓ {result.channel} "
            "• within thresholds"
        )

    # =========================================================
    # Selection
    # =========================================================

    def _row_changed(
        self,
        row: int,
    ):
        self._show_result(
            row
        )

    def _show_result(
        self,
        row: int,
    ):
        if (
            row < 0
            or row
            >= len(
                self.results
            )
        ):
            self.current_result = None

            self._clear_details()

            return

        result = (
            self.results[
                row
            ]
        )

        self.current_result = (
            result
        )

        self.channel_label.setText(
            (
                "Channel: "
                f"{result.channel}"
            )
        )

        if (
            result.channel
            in self.bad_channels
        ):
            state = (
                "MARKED BAD by reviewer"
            )

        elif result.flagged:
            state = (
                "Candidate for review"
            )

        else:
            state = (
                "Within current thresholds"
            )

        self.state_label.setText(
            f"State: {state}"
        )

        self.std_label.setText(
            (
                "Std deviation: "
                f"{result.standard_deviation_uv:.2f} µV"
            )
        )

        self.std_ratio_label.setText(
            (
                "Std ratio: "
                f"{result.std_ratio:.2f}× median"
            )
        )

        self.range_label.setText(
            (
                "Peak-to-peak: "
                f"{result.peak_to_peak_uv:.2f} µV"
            )
        )

        self.extreme_label.setText(
            (
                "Extreme samples: "
                f"{result.extreme_fraction * 100:.2f}%"
            )
        )

        self.flat_label.setText(
            (
                "Near-flat transitions: "
                f"{result.flat_fraction * 100:.2f}%"
            )
        )

        if (
            result.median_correlation
            is None
        ):
            correlation_text = "—"

        else:
            correlation_text = (
                f"{result.median_correlation:.3f}"
            )

        self.correlation_label.setText(
            (
                "Median correlation: "
                f"{correlation_text}"
            )
        )

        if result.reasons:
            self.reason_label.setText(
                "\n\n".join(
                    (
                        f"• {reason}"
                        for reason
                        in result.reasons
                    )
                )
            )

        else:
            self.reason_label.setText(
                (
                    "No configured channel-quality "
                    "thresholds were exceeded."
                )
            )

        self.keep_button.setEnabled(
            True
        )

        self.bad_button.setEnabled(
            True
        )

    # =========================================================
    # Decisions
    # =========================================================

    def _bad_clicked(
        self,
    ):
        if self.current_result is None:
            return

        self.mark_bad_requested.emit(
            self.current_result.channel
        )

    def _keep_clicked(
        self,
    ):
        if self.current_result is None:
            return

        self.keep_requested.emit(
            self.current_result.channel
        )

    # =========================================================
    # Running
    # =========================================================

    def set_running(
        self,
        running: bool,
    ):
        self.analyze_button.setEnabled(
            not running
        )

        if running:
            self.progress_bar.setValue(
                0
            )

            self.status_label.setText(
                (
                    "Analyzing channel quality "
                    "across the recording..."
                )
            )

    def set_progress(
        self,
        value: int,
    ):
        self.progress_bar.setValue(
            value
        )

    def set_error(
        self,
        message: str,
    ):
        self.set_running(
            False
        )

        self.status_label.setText(
            (
                "Channel analysis failed:\n"
                f"{message}"
            )
        )

    # =========================================================
    # Clear
    # =========================================================

    def _clear_details(
        self,
    ):
        self.channel_label.setText(
            "Channel: —"
        )

        self.state_label.setText(
            "State: —"
        )

        self.std_label.setText(
            "Std deviation: —"
        )

        self.std_ratio_label.setText(
            "Std ratio: —"
        )

        self.range_label.setText(
            "Peak-to-peak: —"
        )

        self.extreme_label.setText(
            "Extreme samples: —"
        )

        self.flat_label.setText(
            "Near-flat samples: —"
        )

        self.correlation_label.setText(
            "Median correlation: —"
        )

        self.reason_label.setText(
            "Select a channel."
        )

        self.keep_button.setEnabled(
            False
        )

        self.bad_button.setEnabled(
            False
        )