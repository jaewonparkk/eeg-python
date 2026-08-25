from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from synaptix.models.thresholds import (
    DetectionThresholds,
)


class DetectionPanel(QWidget):
    run_requested = Signal(
        object
    )

    def __init__(self):
        super().__init__()

        self.setMinimumWidth(
            230
        )

        self.setMaximumWidth(
            280
        )

        layout = QVBoxLayout(
            self
        )

        # =====================================================
        # Title
        # =====================================================

        title = QLabel(
            "Detection Settings"
        )

        title.setStyleSheet(
            "font-size: 18px;"
            "font-weight: 600;"
        )

        subtitle = QLabel(
            "Flag suspicious EEG segments "
            "for human review."
        )

        subtitle.setWordWrap(
            True
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            20
        )

        # =====================================================
        # High amplitude
        # =====================================================

        self.amplitude_enabled = QCheckBox(
            "High amplitude"
        )

        self.amplitude_enabled.setChecked(
            True
        )

        self.amplitude_input = (
            QDoubleSpinBox()
        )

        self.amplitude_input.setRange(
            10,
            2000,
        )

        self.amplitude_input.setValue(
            150
        )

        self.amplitude_input.setSuffix(
            " µV"
        )

        self.amplitude_input.setSingleStep(
            10
        )

        layout.addWidget(
            self.amplitude_enabled
        )

        layout.addWidget(
            self.amplitude_input
        )

        layout.addSpacing(
            15
        )

        # =====================================================
        # Rapid transient
        # =====================================================

        self.rapid_enabled = QCheckBox(
            "Rapid transient"
        )

        self.rapid_enabled.setChecked(
            True
        )

        self.rapid_input = (
            QDoubleSpinBox()
        )

        self.rapid_input.setRange(
            5,
            1000,
        )

        self.rapid_input.setValue(
            75
        )

        self.rapid_input.setSuffix(
            " µV/sample"
        )

        self.rapid_input.setSingleStep(
            5
        )

        layout.addWidget(
            self.rapid_enabled
        )

        layout.addWidget(
            self.rapid_input
        )

        layout.addSpacing(
            15
        )

        # =====================================================
        # Flatline
        # =====================================================

        self.flatline_enabled = QCheckBox(
            "Flat / near-flat signal"
        )

        self.flatline_enabled.setChecked(
            True
        )

        flat_duration_label = QLabel(
            "Minimum duration"
        )

        self.flatline_duration_input = (
            QDoubleSpinBox()
        )

        self.flatline_duration_input.setRange(
            0.5,
            30,
        )

        self.flatline_duration_input.setValue(
            2.0
        )

        self.flatline_duration_input.setSuffix(
            " s"
        )

        self.flatline_duration_input.setSingleStep(
            0.5
        )

        flat_tolerance_label = QLabel(
            "Peak-to-peak tolerance"
        )

        self.flatline_tolerance_input = (
            QDoubleSpinBox()
        )

        self.flatline_tolerance_input.setRange(
            0.1,
            20,
        )

        self.flatline_tolerance_input.setValue(
            2.0
        )

        self.flatline_tolerance_input.setSuffix(
            " µV"
        )

        self.flatline_tolerance_input.setSingleStep(
            0.5
        )

        layout.addWidget(
            self.flatline_enabled
        )

        layout.addWidget(
            flat_duration_label
        )

        layout.addWidget(
            self.flatline_duration_input
        )

        layout.addWidget(
            flat_tolerance_label
        )

        layout.addWidget(
            self.flatline_tolerance_input
        )

        layout.addSpacing(
            25
        )

        # =====================================================
        # Run
        # =====================================================

        self.run_button = QPushButton(
            "Run Candidate Scan"
        )

        self.run_button.clicked.connect(
            self._run_clicked
        )

        layout.addWidget(
            self.run_button
        )

        # =====================================================
        # Progress
        # =====================================================

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        self.status_label = QLabel(
            "Ready"
        )

        self.status_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.progress_bar
        )

        layout.addWidget(
            self.status_label
        )

        layout.addStretch()

    # =========================================================
    # Run
    # =========================================================

    def _run_clicked(
        self,
    ):
        thresholds = DetectionThresholds(
            amplitude_enabled=(
                self.amplitude_enabled.isChecked()
            ),
            amplitude_uv=(
                self.amplitude_input.value()
            ),
            rapid_change_enabled=(
                self.rapid_enabled.isChecked()
            ),
            rapid_change_uv=(
                self.rapid_input.value()
            ),
            flatline_enabled=(
                self.flatline_enabled.isChecked()
            ),
            flatline_seconds=(
                self.flatline_duration_input.value()
            ),
            flatline_tolerance_uv=(
                self.flatline_tolerance_input.value()
            ),
        )

        self.run_requested.emit(
            thresholds
        )

    # =========================================================
    # State
    # =========================================================

    def set_running(
        self,
        running: bool,
    ):
        self.run_button.setEnabled(
            not running
        )

        controls = [
            self.amplitude_enabled,
            self.amplitude_input,
            self.rapid_enabled,
            self.rapid_input,
            self.flatline_enabled,
            self.flatline_duration_input,
            self.flatline_tolerance_input,
        ]

        for control in controls:
            control.setEnabled(
                not running
            )

        if running:
            self.progress_bar.setValue(
                0
            )

            self.status_label.setText(
                "Scanning recording..."
            )

    def set_progress(
        self,
        value: int,
    ):
        self.progress_bar.setValue(
            value
        )

    def set_complete(
        self,
        candidate_count: int,
    ):
        self.progress_bar.setValue(
            100
        )

        self.status_label.setText(
            f"{candidate_count} candidates found"
        )

        self.set_running(
            False
        )

    def set_error(
        self,
        message: str,
    ):
        self.status_label.setText(
            f"Detection failed:\n{message}"
        )

        self.set_running(
            False
        )