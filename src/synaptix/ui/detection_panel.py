from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DetectionPanel(QWidget):
    run_requested = Signal(float)

    def __init__(self):
        super().__init__()

        self.setMaximumWidth(220)

        title = QLabel(
            "Detection"
        )

        title.setStyleSheet(
            "font-size: 18px; "
            "font-weight: 600;"
        )

        amplitude_label = QLabel(
            "Amplitude threshold"
        )

        self.amplitude_input = (
            QDoubleSpinBox()
        )

        self.amplitude_input.setRange(
            10.0,
            1000.0,
        )

        self.amplitude_input.setValue(
            150.0
        )

        self.amplitude_input.setSuffix(
            " µV"
        )

        self.amplitude_input.setSingleStep(
            10.0
        )

        self.run_button = QPushButton(
            "Run Detection"
        )

        self.run_button.clicked.connect(
            self._run_clicked
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
            "Ready"
        )

        self.status_label.setWordWrap(
            True
        )

        layout = QVBoxLayout(self)

        layout.addWidget(title)

        layout.addSpacing(20)

        layout.addWidget(
            amplitude_label
        )

        layout.addWidget(
            self.amplitude_input
        )

        layout.addSpacing(20)

        layout.addWidget(
            self.run_button
        )

        layout.addWidget(
            self.progress_bar
        )

        layout.addWidget(
            self.status_label
        )

        layout.addStretch()

    def _run_clicked(self):
        threshold = (
            self.amplitude_input.value()
        )

        self.run_requested.emit(
            threshold
        )

    def set_running(
        self,
        running: bool,
    ):
        self.run_button.setEnabled(
            not running
        )

        self.amplitude_input.setEnabled(
            not running
        )

        if running:
            self.progress_bar.setValue(0)
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

        self.set_running(False)

    def set_error(
        self,
        message: str,
    ):
        self.status_label.setText(
            f"Detection failed:\n{message}"
        )

        self.set_running(False)