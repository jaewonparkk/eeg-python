from PySide6.QtCore import (
    Signal,
)

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from synaptix.core.recording import (
    Recording,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
    PipelineStep,
    StepType,
)
from synaptix.processing.step_registry import (
    definition_for,
)
from synaptix.processing.warnings import (
    PipelineWarningEngine,
)


class StepInspector(QWidget):
    step_changed = Signal(
        object
    )

    def __init__(
        self,
    ):
        super().__init__()

        self.current_step: (
            PipelineStep | None
        ) = None

        self.pipeline: (
            PipelineConfiguration | None
        ) = None

        self.recording: (
            Recording | None
        ) = None

        self.setMinimumWidth(
            300
        )

        # =====================================================
        # Header
        # =====================================================

        self.title_label = QLabel(
            "Step Details"
        )

        self.title_label.setStyleSheet(
            (
                "font-size: 18px;"
                "font-weight: 600;"
            )
        )

        self.description_label = QLabel(
            "Select a pipeline step."
        )

        self.description_label.setWordWrap(
            True
        )

        # =====================================================
        # Context
        # =====================================================

        self.function_label = QLabel(
            "Preview function: —"
        )

        self.export_function_label = QLabel(
            "Export function: —"
        )

        self.input_label = QLabel(
            "Input: —"
        )

        self.output_label = QLabel(
            "Output: —"
        )

        self.variables_label = QLabel(
            "Variables: —"
        )

        # =====================================================
        # Parameter stack
        # =====================================================

        self.parameter_stack = (
            QStackedWidget()
        )

        self.bandpass_widget = (
            self._build_bandpass_widget()
        )

        self.notch_widget = (
            self._build_notch_widget()
        )

        self.reference_widget = (
            self._build_reference_widget()
        )

        self.parameter_stack.addWidget(
            self.bandpass_widget
        )

        self.parameter_stack.addWidget(
            self.notch_widget
        )

        self.parameter_stack.addWidget(
            self.reference_widget
        )

        # =====================================================
        # Apply
        # =====================================================

        self.apply_button = QPushButton(
            "Apply Step Settings"
        )

        self.apply_button.clicked.connect(
            self._apply_settings
        )

        # =====================================================
        # Warnings
        # =====================================================

        warning_title = QLabel(
            "Warnings / Context"
        )

        warning_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.warning_label = QLabel(
            "No warnings."
        )

        self.warning_label.setWordWrap(
            True
        )

        # =====================================================
        # Layout
        # =====================================================

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.description_label
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            self.function_label
        )

        layout.addWidget(
            self.export_function_label
        )

        layout.addWidget(
            self.input_label
        )

        layout.addWidget(
            self.output_label
        )

        layout.addWidget(
            self.variables_label
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            self.parameter_stack
        )

        layout.addWidget(
            self.apply_button
        )

        layout.addSpacing(
            20
        )

        layout.addWidget(
            warning_title
        )

        layout.addWidget(
            self.warning_label
        )

        layout.addStretch()

    # =========================================================
    # Parameter widgets
    # =========================================================

    def _build_bandpass_widget(
        self,
    ) -> QWidget:
        widget = QWidget()

        form = QFormLayout(
            widget
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

        self.highpass_input.setSuffix(
            " Hz"
        )

        self.lowpass_input = (
            QDoubleSpinBox()
        )

        self.lowpass_input.setRange(
            0.5,
            500.0,
        )

        self.lowpass_input.setDecimals(
            1
        )

        self.lowpass_input.setSuffix(
            " Hz"
        )

        self.filter_order_input = (
            QSpinBox()
        )

        self.filter_order_input.setRange(
            1,
            10,
        )

        form.addRow(
            "High-pass",
            self.highpass_input,
        )

        form.addRow(
            "Low-pass",
            self.lowpass_input,
        )

        form.addRow(
            "Filter order",
            self.filter_order_input,
        )

        return widget

    def _build_notch_widget(
        self,
    ) -> QWidget:
        widget = QWidget()

        form = QFormLayout(
            widget
        )

        self.notch_frequency_input = (
            QDoubleSpinBox()
        )

        self.notch_frequency_input.setRange(
            1.0,
            500.0,
        )

        self.notch_frequency_input.setSuffix(
            " Hz"
        )

        self.notch_q_input = (
            QDoubleSpinBox()
        )

        self.notch_q_input.setRange(
            1.0,
            100.0,
        )

        form.addRow(
            "Frequency",
            self.notch_frequency_input,
        )

        form.addRow(
            "Quality factor",
            self.notch_q_input,
        )

        return widget

    def _build_reference_widget(
        self,
    ) -> QWidget:
        widget = QWidget()

        form = QFormLayout(
            widget
        )

        self.reference_type_label = QLabel(
            "Average"
        )

        self.excluded_channels_input = (
            QLineEdit()
        )

        self.excluded_channels_input.setPlaceholderText(
            "Example: Fp1, T3"
        )

        form.addRow(
            "Reference",
            self.reference_type_label,
        )

        form.addRow(
            "Exclude channels",
            self.excluded_channels_input,
        )

        return widget

    # =========================================================
    # Set step
    # =========================================================

    def set_step(
        self,
        step: PipelineStep,
        pipeline: PipelineConfiguration,
        recording: Recording | None,
    ):
        self.current_step = step
        self.pipeline = pipeline
        self.recording = recording

        definition = (
            definition_for(
                step.step_type
            )
        )

        self.title_label.setText(
            definition.display_name
        )

        self.description_label.setText(
            definition.description
        )

        self.function_label.setText(
            (
                "Preview function: "
                f"{definition.preview_function}"
            )
        )

        self.export_function_label.setText(
            (
                "Generated script: "
                f"{definition.export_function}"
            )
        )

        # =====================================================
        # Input metadata
        # =====================================================

        if recording is None:
            self.input_label.setText(
                "Input: No EEG loaded"
            )

            self.output_label.setText(
                "Output: —"
            )

            self.variables_label.setText(
                "Variables: —"
            )

        else:
            self.input_label.setText(
                (
                    "Input: "
                    f"{recording.eeg_channel_count} "
                    "EEG channels • "
                    f"{recording.sampling_frequency:.0f} Hz"
                )
            )

            self.output_label.setText(
                (
                    "Output: "
                    f"{recording.eeg_channel_count} "
                    "EEG channels"
                )
            )

            self.variables_label.setText(
                (
                    "Variables: continuous "
                    "signal samples × channels"
                )
            )

        # =====================================================
        # Parameters
        # =====================================================

        if (
            step.step_type
            == StepType.BANDPASS
        ):
            self.parameter_stack.setCurrentWidget(
                self.bandpass_widget
            )

            self.highpass_input.setValue(
                float(
                    step.parameters.get(
                        "highpass_hz",
                        0.5,
                    )
                )
            )

            self.lowpass_input.setValue(
                float(
                    step.parameters.get(
                        "lowpass_hz",
                        45.0,
                    )
                )
            )

            self.filter_order_input.setValue(
                int(
                    step.parameters.get(
                        "order",
                        4,
                    )
                )
            )

        elif (
            step.step_type
            == StepType.NOTCH
        ):
            self.parameter_stack.setCurrentWidget(
                self.notch_widget
            )

            self.notch_frequency_input.setValue(
                float(
                    step.parameters.get(
                        "frequency_hz",
                        60.0,
                    )
                )
            )

            self.notch_q_input.setValue(
                float(
                    step.parameters.get(
                        "quality_factor",
                        30.0,
                    )
                )
            )

        elif (
            step.step_type
            == StepType.AVERAGE_REFERENCE
        ):
            self.parameter_stack.setCurrentWidget(
                self.reference_widget
            )

            excluded = list(
                step.parameters.get(
                    "exclude_channels",
                    [],
                )
            )

            self.excluded_channels_input.setText(
                ", ".join(
                    excluded
                )
            )

        self.refresh_warnings()

    # =========================================================
    # Apply
    # =========================================================

    def _apply_settings(
        self,
    ):
        if self.current_step is None:
            return

        step = (
            self.current_step
        )

        if (
            step.step_type
            == StepType.BANDPASS
        ):
            step.parameters[
                "highpass_hz"
            ] = (
                self.highpass_input.value()
            )

            step.parameters[
                "lowpass_hz"
            ] = (
                self.lowpass_input.value()
            )

            step.parameters[
                "order"
            ] = (
                self.filter_order_input.value()
            )

        elif (
            step.step_type
            == StepType.NOTCH
        ):
            step.parameters[
                "frequency_hz"
            ] = (
                self.notch_frequency_input.value()
            )

            step.parameters[
                "quality_factor"
            ] = (
                self.notch_q_input.value()
            )

        elif (
            step.step_type
            == StepType.AVERAGE_REFERENCE
        ):
            text = (
                self.excluded_channels_input.text()
            )

            excluded = [
                channel.strip()
                for channel
                in text.split(",")
                if channel.strip()
            ]

            step.parameters[
                "exclude_channels"
            ] = excluded

        self.refresh_warnings()

        self.step_changed.emit(
            step
        )

    # =========================================================
    # Warnings
    # =========================================================

    def refresh_warnings(
        self,
    ):
        if (
            self.current_step is None
            or self.pipeline is None
        ):
            self.warning_label.setText(
                "No warnings."
            )

            return

        warnings = (
            PipelineWarningEngine
            .warnings_for_step(
                step=self.current_step,
                pipeline=self.pipeline,
                recording=self.recording,
            )
        )

        if not warnings:
            self.warning_label.setText(
                "✓ No current warnings."
            )

            return

        self.warning_label.setText(
            "\n\n".join(
                (
                    f"⚠ {warning}"
                    for warning
                    in warnings
                )
            )
        )