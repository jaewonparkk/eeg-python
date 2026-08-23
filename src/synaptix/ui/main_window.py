from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from synaptix.core.recording import Recording
from synaptix.ui.eeg_viewer import EEGViewer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.recording: Recording | None = None

        self.setWindowTitle(
            "Synaptix EEG Workbench"
        )

        self.resize(
            1200,
            800,
        )

        self.open_button = QPushButton(
            "Open EEG"
        )

        self.open_button.clicked.connect(
            self.open_eeg
        )

        self.info_label = QLabel(
            "Open an EEG recording."
        )

        self.viewer = EEGViewer()

        layout = QVBoxLayout()

        layout.addWidget(
            self.open_button
        )

        layout.addWidget(
            self.info_label
        )

        layout.addWidget(
            self.viewer,
            stretch=1,
        )

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(
            container
        )

    def open_eeg(self):
        filepath, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Open EEG Recording",
                "",
                (
                    "EEG Files "
                    "(*.edf *.bdf *.fif *.set);;"
                    "All Files (*)"
                ),
            )
        )

        if not filepath:
            return

        try:
            recording = (
                Recording.from_file(
                    filepath
                )
            )

            self.recording = recording

            self.info_label.setText(
                f"{recording.name}  •  "
                f"{recording.channel_count} channels  •  "
                f"{recording.sampling_frequency:.0f} Hz  •  "
                f"{recording.duration_seconds / 60:.1f} min"
            )

            self.viewer.set_recording(
                recording
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Unable to open EEG",
                str(error),
            )