from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class ScriptPreviewPanel(QWidget):
    def __init__(
        self,
    ):
        super().__init__()

        title = QLabel(
            "Generated Reproducible Script"
        )

        title.setStyleSheet(
            (
                "font-size: 15px;"
                "font-weight: 600;"
            )
        )

        subtitle = QLabel(
            (
                "This script mirrors the "
                "enabled pipeline steps and "
                "their current order."
            )
        )

        self.editor = (
            QPlainTextEdit()
        )

        self.editor.setReadOnly(
            True
        )

        self.editor.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
        )

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addWidget(
            self.editor
        )

    def set_script(
        self,
        script: str,
    ):
        self.editor.setPlainText(
            script
        )