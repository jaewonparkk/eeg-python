from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from synaptix.models.processing import (
    ProcessingSettings,
)


class ProcessingPanel(QWidget):
    apply_requested = Signal(
        object
    )

    def __init__(
        self,
    ):
        super().__init__()

        self.setMinimumWidth(
            240
        )

        self.setMaximumWidth(
            300
        )

        layout = QVBoxLayout(
            self
        )

        # =====================================================
        # Title
        # =====================================================

        title = QLabel(
            "Processing Preview"
        )

        title.setStyleSheet(
            "font-size: 18px;"
            "font-weight: 600;"
        )

        description = QLabel(
            (
                "Preview preprocessing without "
                "modifying the original EEG."
            )
        )

        description.setWordWrap(
            True
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            description
        )

        layout.addSpacing(
            20
        )

        # =====================================================
        # Band-pass
        # =====================================================

        self.bandpass_enabled = (
            QCheckBox(
                "Band-pass filter"
            )
        )

        self.bandpass_enabled.setChecked(
            True
        )

        highpass_label = QLabel(
            "High-pass"
        )

        self.highpass_input = (
            QDoubleSpinBox()
        )

        self.highpass_input.setRange(
            0.1,
            200.0,
        )

        self.highpass_input.setDecimals(
            1
        )

        self.highpass_input.setValue(
            0.5
        )

        self.highpass_input.setSuffix(
            " Hz"
        )

        self.highpass_input.setSingleStep(
            0.5
        )

        lowpass_label = QLabel(
            "Low-pass"
        )

        self.lowpass_input = (
            QDoubleSpinBox()
        )

        self.lowpass_input.setRange(
            1.0,
            500.0,
        )

        self.lowpass_input.setDecimals(
            1
        )

        self.lowpass_input.setValue(
            45.0
        )

        self.lowpass_input.setSuffix(
            " Hz"
        )

        self.lowpass_input.setSingleStep(
            1.0
        )

        order_label = QLabel(
            "Filter order"
        )

        self.filter_order_input = (
            QSpinBox()
        )

        self.filter_order_input.setRange(
            1,
            10,
        )

        self.filter_order_input.setValue(
            4
        )

        layout.addWidget(
            self.bandpass_enabled
        )

        layout.addWidget(
            highpass_label
        )

        layout.addWidget(
            self.highpass_input
        )

        layout.addWidget(
            lowpass_label
        )

        layout.addWidget(
            self.lowpass_input
        )

        layout.addWidget(
            order_label
        )

        layout.addWidget(
            self.filter_order_input
        )

        layout.addSpacing(
            20
        )

        # =====================================================
        # Notch
        # =====================================================

        self.notch_enabled = (
            QCheckBox(
                "Notch filter"
            )
        )

        self.notch_enabled.setChecked(
            False
        )

        notch_label = QLabel(
            "Power-line frequency"
        )

        self.notch_selector = (
            QComboBox()
        )

        self.notch_selector.addItems(
            [
                "50 Hz",
                "60 Hz",
            ]
        )

        self.notch_selector.setCurrentText(
            "60 Hz"
        )

        layout.addWidget(
            self.notch_enabled
        )

        layout.addWidget(
            notch_label
        )

        layout.addWidget(
            self.notch_selector
        )

        layout.addSpacing(
            25
        )

        # =====================================================
        # Apply
        # =====================================================

        self.apply_button = QPushButton(
            "Apply Preview"
        )

        self.apply_button.clicked.connect(
            self._apply_clicked
        )

        self.status_label = QLabel(
            (
                "Current preview:\n"
                "Band-pass 0.5–45 Hz"
            )
        )

        self.status_label.setWordWrap(
            True
        )

        layout.addWidget(
            self.apply_button
        )

        layout.addWidget(
            self.status_label
        )

        layout.addStretch()

    # =========================================================
    # Settings
    # =========================================================

    def current_settings(
        self,
    ) -> ProcessingSettings:
        notch_text = (
            self.notch_selector.currentText()
        )

        notch_frequency = float(
            notch_text.split()[0]
        )

        return ProcessingSettings(
            bandpass_enabled=(
                self.bandpass_enabled.isChecked()
            ),
            highpass_hz=(
                self.highpass_input.value()
            ),
            lowpass_hz=(
                self.lowpass_input.value()
            ),
            filter_order=(
                self.filter_order_input.value()
            ),
            notch_enabled=(
                self.notch_enabled.isChecked()
            ),
            notch_hz=(
                notch_frequency
            ),
        )

    # =========================================================
    # Apply
    # =========================================================

    def _apply_clicked(
        self,
    ):
        settings = (
            self.current_settings()
        )

        if (
            settings.bandpass_enabled
            and settings.lowpass_hz
            <= settings.highpass_hz
        ):
            self.status_label.setText(
                (
                    "Invalid settings:\n"
                    "Low-pass must be greater "
                    "than high-pass."
                )
            )

            return

        self.apply_requested.emit(
            settings
        )

        self.set_applied(
            settings
        )

    # =========================================================
    # Status
    # =========================================================

    def set_applied(
        self,
        settings: ProcessingSettings,
    ):
        descriptions: list[str] = []

        if settings.bandpass_enabled:
            descriptions.append(
                (
                    f"{settings.highpass_hz:g}"
                    f"–"
                    f"{settings.lowpass_hz:g} Hz"
                    f" band-pass"
                )
            )

        if settings.notch_enabled:
            descriptions.append(
                (
                    f"{settings.notch_hz:g} Hz"
                    " notch"
                )
            )

        if not descriptions:
            description = (
                "No processing"
            )

        else:
            description = (
                " + ".join(
                    descriptions
                )
            )

        self.status_label.setText(
            (
                "Current preview:\n"
                f"{description}"
            )
        )