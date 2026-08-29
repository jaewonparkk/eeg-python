from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from synaptix.models.bridge import (
    BridgeCandidate,
    BridgeDetectionSettings,
)


class BridgePanel(QWidget):
    analyze_requested = Signal(object)
    confirm_requested = Signal(object)
    reject_requested = Signal(object)

    def __init__(self):
        super().__init__()

        self.candidates: list[BridgeCandidate] = []
        self.current_candidate: BridgeCandidate | None = None

        # =====================================================
        # Header
        # =====================================================

        title = QLabel(
            "Electrode Bridge Detection"
        )

        title.setStyleSheet(
            "font-size: 18px;"
            "font-weight: 600;"
        )

        description = QLabel(
            (
                "Detect EEG electrode pairs with unusually "
                "low electrical distance. Detection results "
                "require human review and are not automatically "
                "removed or corrected."
            )
        )

        description.setWordWrap(
            True
        )

        # =====================================================
        # Settings
        # =====================================================

        self.enabled_input = QCheckBox(
            "Enable bridge detection"
        )

        self.enabled_input.setChecked(
            True
        )

        self.lm_cutoff_input = (
            QDoubleSpinBox()
        )

        self.lm_cutoff_input.setRange(
            0.1,
            100.0,
        )

        self.lm_cutoff_input.setDecimals(
            2
        )

        self.lm_cutoff_input.setValue(
            16.0
        )

        self.lm_cutoff_input.setSuffix(
            " µV²"
        )

        self.epoch_threshold_input = (
            QDoubleSpinBox()
        )

        self.epoch_threshold_input.setRange(
            1.0,
            100.0,
        )

        self.epoch_threshold_input.setDecimals(
            1
        )

        self.epoch_threshold_input.setValue(
            50.0
        )

        self.epoch_threshold_input.setSuffix(
            " %"
        )

        self.low_frequency_input = (
            QDoubleSpinBox()
        )

        self.low_frequency_input.setRange(
            0.1,
            100.0,
        )

        self.low_frequency_input.setDecimals(
            1
        )

        self.low_frequency_input.setValue(
            0.5
        )

        self.low_frequency_input.setSuffix(
            " Hz"
        )

        self.high_frequency_input = (
            QDoubleSpinBox()
        )

        self.high_frequency_input.setRange(
            0.5,
            500.0,
        )

        self.high_frequency_input.setDecimals(
            1
        )

        self.high_frequency_input.setValue(
            30.0
        )

        self.high_frequency_input.setSuffix(
            " Hz"
        )

        self.epoch_duration_input = (
            QDoubleSpinBox()
        )

        self.epoch_duration_input.setRange(
            0.5,
            30.0,
        )

        self.epoch_duration_input.setDecimals(
            1
        )

        self.epoch_duration_input.setValue(
            2.0
        )

        self.epoch_duration_input.setSuffix(
            " s"
        )

        settings_form = QFormLayout()

        settings_form.addRow(
            "LM search cutoff",
            self.lm_cutoff_input,
        )

        settings_form.addRow(
            "Epoch threshold",
            self.epoch_threshold_input,
        )

        settings_form.addRow(
            "Low frequency",
            self.low_frequency_input,
        )

        settings_form.addRow(
            "High frequency",
            self.high_frequency_input,
        )

        settings_form.addRow(
            "Epoch duration",
            self.epoch_duration_input,
        )

        # =====================================================
        # Analyze
        # =====================================================

        self.analyze_button = QPushButton(
            "Run Bridge Detection"
        )

        self.analyze_button.clicked.connect(
            self._analyze_clicked
        )

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        self.status_label = QLabel(
            "No bridge analysis yet."
        )

        self.status_label.setWordWrap(
            True
        )

        # =====================================================
        # Results
        # =====================================================

        results_title = QLabel(
            "Bridge Candidates"
        )

        results_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.list_widget = QListWidget()

        self.list_widget.currentRowChanged.connect(
            self._row_changed
        )

        # =====================================================
        # Details
        # =====================================================

        details_title = QLabel(
            "Pair Details"
        )

        details_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.pair_label = QLabel(
            "Pair: —"
        )

        self.state_label = QLabel(
            "State: —"
        )

        self.median_label = QLabel(
            "Median electrical distance: —"
        )

        self.minimum_label = QLabel(
            "Minimum electrical distance: —"
        )

        self.fraction_label = QLabel(
            "Below search cutoff: —"
        )

        self.epoch_label = QLabel(
            "Epochs analyzed: —"
        )

        why_title = QLabel(
            "Why was this flagged?"
        )

        why_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.reason_label = QLabel(
            "Select a bridge candidate."
        )

        self.reason_label.setWordWrap(
            True
        )

        # =====================================================
        # Decisions
        # =====================================================

        self.reject_button = QPushButton(
            "Keep Pair / Not Bridged"
        )

        self.confirm_button = QPushButton(
            "Confirm Bridge"
        )

        self.reject_button.clicked.connect(
            self._reject_clicked
        )

        self.confirm_button.clicked.connect(
            self._confirm_clicked
        )

        self.reject_button.setEnabled(
            False
        )

        self.confirm_button.setEnabled(
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
            description
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            self.enabled_input
        )

        layout.addLayout(
            settings_form
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
            results_title
        )

        layout.addWidget(
            self.list_widget,
            stretch=1,
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            details_title
        )

        layout.addWidget(
            self.pair_label
        )

        layout.addWidget(
            self.state_label
        )

        layout.addWidget(
            self.median_label
        )

        layout.addWidget(
            self.minimum_label
        )

        layout.addWidget(
            self.fraction_label
        )

        layout.addWidget(
            self.epoch_label
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
            self.reject_button
        )

        layout.addWidget(
            self.confirm_button
        )

    # =========================================================
    # Settings
    # =========================================================

    def current_settings(
        self,
    ) -> BridgeDetectionSettings:
        return BridgeDetectionSettings(
            enabled=(
                self.enabled_input.isChecked()
            ),
            lm_cutoff_uv2=(
                self.lm_cutoff_input.value()
            ),
            epoch_threshold=(
                self.epoch_threshold_input.value()
                / 100.0
            ),
            low_frequency_hz=(
                self.low_frequency_input.value()
            ),
            high_frequency_hz=(
                self.high_frequency_input.value()
            ),
            epoch_duration_seconds=(
                self.epoch_duration_input.value()
            ),
        )

    def set_settings(
        self,
        settings: BridgeDetectionSettings,
    ):
        self.enabled_input.setChecked(
            settings.enabled
        )

        self.lm_cutoff_input.setValue(
            settings.lm_cutoff_uv2
        )

        self.epoch_threshold_input.setValue(
            settings.epoch_threshold
            * 100.0
        )

        self.low_frequency_input.setValue(
            settings.low_frequency_hz
        )

        self.high_frequency_input.setValue(
            settings.high_frequency_hz
        )

        self.epoch_duration_input.setValue(
            settings.epoch_duration_seconds
        )

    def _analyze_clicked(
        self,
    ):
        self.analyze_requested.emit(
            self.current_settings()
        )

    # =========================================================
    # Results
    # =========================================================

    def set_results(
        self,
        candidates: list[BridgeCandidate],
    ):
        self.candidates = candidates
        self.current_candidate = None

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            100
        )

        self.set_running(
            False
        )

        if candidates:
            self.status_label.setText(
                (
                    f"{len(candidates)} possible "
                    "bridge pair(s) detected."
                )
            )

        else:
            self.status_label.setText(
                (
                    "No electrode bridge pairs "
                    "were detected with the "
                    "current settings."
                )
            )

        self._populate_list()

    def clear_results(
        self,
    ):
        self.candidates = []
        self.current_candidate = None

        self.list_widget.clear()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        self.status_label.setText(
            "No bridge analysis yet."
        )

        self._clear_details()

    # =========================================================
    # Confirmed state
    # =========================================================

    def sync_confirmed_pairs(
        self,
        pairs: list[
            tuple[str, str]
        ],
    ):
        confirmed_pairs = {
            frozenset(
                pair
            )
            for pair in pairs
        }

        selected_pair = None

        if (
            self.current_candidate
            is not None
        ):
            selected_pair = (
                self.current_candidate.channel_a,
                self.current_candidate.channel_b,
            )

        for candidate in self.candidates:
            pair = frozenset(
                (
                    candidate.channel_a,
                    candidate.channel_b,
                )
            )

            if pair in confirmed_pairs:
                candidate.confirmed = True

            elif (
                candidate.confirmed
                is True
            ):
                candidate.confirmed = None

        self._populate_list(
            selected_pair=(
                selected_pair
            )
        )

    # =========================================================
    # List
    # =========================================================

    def _populate_list(
        self,
        selected_pair: (
            tuple[str, str]
            | None
        ) = None,
    ):
        self.list_widget.blockSignals(
            True
        )

        self.list_widget.clear()

        selected_row = 0

        for index, candidate in enumerate(
            self.candidates
        ):
            self.list_widget.addItem(
                self._item_text(
                    candidate
                )
            )

            if (
                selected_pair is not None
                and set(
                    selected_pair
                )
                == {
                    candidate.channel_a,
                    candidate.channel_b,
                }
            ):
                selected_row = index

        if self.candidates:
            self.list_widget.setCurrentRow(
                selected_row
            )

        self.list_widget.blockSignals(
            False
        )

        if self.candidates:
            self._show_candidate(
                selected_row
            )

        else:
            self._clear_details()

    @staticmethod
    def _item_text(
        candidate: BridgeCandidate,
    ) -> str:
        if (
            candidate.confirmed
            is True
        ):
            status = "● CONFIRMED"

        elif (
            candidate.confirmed
            is False
        ):
            status = "× REJECTED"

        else:
            status = "⚠ REVIEW"

        return (
            f"{status} • "
            f"{candidate.channel_a}"
            " ↔ "
            f"{candidate.channel_b}"
        )

    # =========================================================
    # Selection
    # =========================================================

    def _row_changed(
        self,
        row: int,
    ):
        self._show_candidate(
            row
        )

    def _show_candidate(
        self,
        row: int,
    ):
        if (
            row < 0
            or row
            >= len(
                self.candidates
            )
        ):
            self._clear_details()
            return

        candidate = (
            self.candidates[
                row
            ]
        )

        self.current_candidate = (
            candidate
        )

        self.pair_label.setText(
            (
                "Pair: "
                f"{candidate.channel_a}"
                " ↔ "
                f"{candidate.channel_b}"
            )
        )

        if (
            candidate.confirmed
            is True
        ):
            state = "Confirmed bridge"

        elif (
            candidate.confirmed
            is False
        ):
            state = "Rejected by reviewer"

        else:
            state = "Candidate for review"

        self.state_label.setText(
            f"State: {state}"
        )

        self.median_label.setText(
            (
                "Median electrical distance: "
                f"{candidate.median_electrical_distance_uv2:.3f} "
                "µV²"
            )
        )

        self.minimum_label.setText(
            (
                "Minimum electrical distance: "
                f"{candidate.minimum_electrical_distance_uv2:.3f} "
                "µV²"
            )
        )

        self.fraction_label.setText(
            (
                "Below search cutoff: "
                f"{candidate.fraction_below_search_cutoff * 100:.1f}%"
            )
        )

        self.epoch_label.setText(
            (
                "Epochs analyzed: "
                f"{candidate.epoch_count}"
            )
        )

        self.reason_label.setText(
            candidate.reason
        )

        self.reject_button.setEnabled(
            True
        )

        self.confirm_button.setEnabled(
            True
        )

    # =========================================================
    # Decisions
    # =========================================================

    def _confirm_clicked(
        self,
    ):
        if self.current_candidate is None:
            return

        self.confirm_requested.emit(
            self.current_candidate
        )

    def _reject_clicked(
        self,
    ):
        if self.current_candidate is None:
            return

        self.reject_requested.emit(
            self.current_candidate
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
            self.progress_bar.setRange(
                0,
                0,
            )

            self.status_label.setText(
                (
                    "Computing pairwise "
                    "electrical distances..."
                )
            )

        else:
            self.progress_bar.setRange(
                0,
                100,
            )

    def set_error(
        self,
        message: str,
    ):
        self.set_running(
            False
        )

        self.progress_bar.setValue(
            0
        )

        self.status_label.setText(
            (
                "Bridge detection failed:\n"
                f"{message}"
            )
        )

    # =========================================================
    # Clear details
    # =========================================================

    def _clear_details(
        self,
    ):
        self.current_candidate = None

        self.pair_label.setText(
            "Pair: —"
        )

        self.state_label.setText(
            "State: —"
        )

        self.median_label.setText(
            "Median electrical distance: —"
        )

        self.minimum_label.setText(
            "Minimum electrical distance: —"
        )

        self.fraction_label.setText(
            "Below search cutoff: —"
        )

        self.epoch_label.setText(
            "Epochs analyzed: —"
        )

        self.reason_label.setText(
            "Select a bridge candidate."
        )

        self.reject_button.setEnabled(
            False
        )

        self.confirm_button.setEnabled(
            False
        )