from pathlib import Path

from PySide6.QtCore import (
    Signal,
)

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ScriptPreviewPanel(QWidget):
    apply_requested = Signal(
        str
    )

    regenerate_requested = Signal()

    def __init__(
        self,
    ):
        super().__init__()

        # =====================================================
        # Header
        # =====================================================

        title = QLabel(
            "Pipeline Script"
        )

        title.setStyleSheet(
            (
                "font-size: 15px;"
                "font-weight: 600;"
            )
        )

        subtitle = QLabel(
            (
                "Edit the configuration values or "
                "PIPELINE_ORDER, then apply them "
                "back to the Synaptix pipeline."
            )
        )

        subtitle.setWordWrap(
            True
        )

        # =====================================================
        # Editor
        # =====================================================

        self.editor = (
            QPlainTextEdit()
        )

        self.editor.setReadOnly(
            False
        )

        self.editor.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
        )

        self.editor.setPlaceholderText(
            (
                "Synaptix will generate a "
                "reproducible preprocessing "
                "script here."
            )
        )

        # =====================================================
        # Buttons
        # =====================================================

        self.apply_button = QPushButton(
            "Apply Script to Pipeline"
        )

        self.regenerate_button = QPushButton(
            "Regenerate from Pipeline"
        )

        self.save_button = QPushButton(
            "Save .py"
        )

        self.apply_button.clicked.connect(
            self._apply_clicked
        )

        self.regenerate_button.clicked.connect(
            self.regenerate_requested.emit
        )

        self.save_button.clicked.connect(
            self._save_clicked
        )

        button_layout = QHBoxLayout()

        button_layout.addWidget(
            self.apply_button
        )

        button_layout.addWidget(
            self.regenerate_button
        )

        button_layout.addWidget(
            self.save_button
        )

        # =====================================================
        # Status
        # =====================================================

        self.status_label = QLabel(
            (
                "Pipeline-generated script. "
                "Safe configuration parsing only."
            )
        )

        self.status_label.setWordWrap(
            True
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

        layout.addLayout(
            button_layout
        )

        layout.addWidget(
            self.status_label
        )

        layout.addWidget(
            self.editor,
            stretch=1,
        )

    # =========================================================
    # Content
    # =========================================================

    def set_script(
        self,
        script: str,
    ):
        self.editor.setPlainText(
            script
        )

    def script(
        self,
    ) -> str:
        return self.editor.toPlainText()

    # =========================================================
    # Apply
    # =========================================================

    def _apply_clicked(
        self,
    ):
        script = (
            self.editor.toPlainText()
        )

        self.apply_requested.emit(
            script
        )

    # =========================================================
    # Status
    # =========================================================

    def set_status(
        self,
        message: str,
    ):
        self.status_label.setText(
            message
        )

    # =========================================================
    # Save
    # =========================================================

    def _save_clicked(
        self,
    ):
        filepath, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Save Synaptix Pipeline Script",
                "synaptix_pipeline.py",
                "Python Files (*.py)",
            )
        )

        if not filepath:
            return

        path = Path(
            filepath
        )

        try:
            path.write_text(
                self.editor.toPlainText(),
                encoding="utf-8",
            )

            self.set_status(
                f"Saved script: {path.name}"
            )

        except OSError as error:
            self.set_status(
                (
                    "Unable to save script: "
                    f"{error}"
                )
            )