from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from synaptix.core.recording import (
    Recording,
)
from synaptix.models.processing import (
    ProcessingSettings,
)
from synaptix.models.thresholds import (
    DetectionThresholds,
)
from synaptix.ui.detection_panel import (
    DetectionPanel,
)
from synaptix.ui.eeg_viewer import (
    EEGViewer,
)
from synaptix.ui.processing_panel import (
    ProcessingPanel,
)
from synaptix.ui.review_panel import (
    ReviewPanel,
)
from synaptix.ui.workers import (
    DetectionWorker,
)


class MainWindow(QMainWindow):
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

        self.detection_worker: (
            DetectionWorker | None
        ) = None

        # =====================================================
        # Window
        # =====================================================

        self.setWindowTitle(
            "Synaptix EEG Workbench"
        )

        self.resize(
            1600,
            1000,
        )

        # =====================================================
        # Top bar
        # =====================================================

        self.open_button = QPushButton(
            "Open EEG"
        )

        self.open_button.clicked.connect(
            self.open_eeg
        )

        self.info_label = QLabel(
            "Open an EEG recording to begin."
        )

        self.info_label.setStyleSheet(
            "font-weight: 500;"
        )

        top_layout = QHBoxLayout()

        top_layout.addWidget(
            self.open_button
        )

        top_layout.addWidget(
            self.info_label,
            stretch=1,
        )

        # =====================================================
        # Left panels
        # =====================================================

        self.detection_panel = (
            DetectionPanel()
        )

        self.processing_panel = (
            ProcessingPanel()
        )

        self.left_tabs = (
            QTabWidget()
        )

        self.left_tabs.addTab(
            self.detection_panel,
            "Detection",
        )

        self.left_tabs.addTab(
            self.processing_panel,
            "Processing",
        )

        self.left_tabs.setMinimumWidth(
            270
        )

        self.left_tabs.setMaximumWidth(
            330
        )

        # =====================================================
        # Viewer
        # =====================================================

        self.viewer = EEGViewer()

        # =====================================================
        # Review
        # =====================================================

        self.review_panel = (
            ReviewPanel()
        )

        # =====================================================
        # Signals
        # =====================================================

        self.detection_panel.run_requested.connect(
            self.run_detection
        )

        self.processing_panel.apply_requested.connect(
            self.apply_processing_preview
        )

        self.review_panel.candidate_selected.connect(
            self.viewer.go_to_candidate
        )

        self.review_panel.candidate_updated.connect(
            self._candidate_updated
        )

        # =====================================================
        # Main workspace
        # =====================================================

        self.splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        self.splitter.addWidget(
            self.left_tabs
        )

        self.splitter.addWidget(
            self.viewer
        )

        self.splitter.addWidget(
            self.review_panel
        )

        self.splitter.setStretchFactor(
            0,
            0,
        )

        self.splitter.setStretchFactor(
            1,
            1,
        )

        self.splitter.setStretchFactor(
            2,
            0,
        )

        self.splitter.setSizes(
            [
                300,
                980,
                320,
            ]
        )

        # =====================================================
        # Root
        # =====================================================

        root_layout = QVBoxLayout()

        root_layout.addLayout(
            top_layout
        )

        root_layout.addWidget(
            self.splitter,
            stretch=1,
        )

        container = QWidget()

        container.setLayout(
            root_layout
        )

        self.setCentralWidget(
            container
        )

    # =========================================================
    # Open EEG
    # =========================================================

    def open_eeg(
        self,
    ):
        if (
            self.detection_worker
            is not None
            and self.detection_worker.isRunning()
        ):
            QMessageBox.warning(
                self,
                "Detection in progress",
                (
                    "Wait for the current candidate "
                    "scan to finish before opening "
                    "another EEG."
                ),
            )

            return

        filepath, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Open EEG Recording",
                "",
                (
                    "EEG Files "
                    "(*.edf *.bdf *.fif *.set);;"
                    "EEGLAB Files (*.set);;"
                    "EDF Files (*.edf);;"
                    "BDF Files (*.bdf);;"
                    "FIF Files (*.fif);;"
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

            self.recording = (
                recording
            )

            # -------------------------------------------------
            # Reset candidate state
            # -------------------------------------------------

            self.viewer.set_artifact_candidates(
                []
            )

            self.review_panel.set_candidates(
                []
            )

            # -------------------------------------------------
            # Processing defaults
            # -------------------------------------------------

            processing_settings = (
                self.processing_panel.current_settings()
            )

            self.viewer.set_processing_settings(
                processing_settings
            )

            self.processing_panel.set_applied(
                processing_settings
            )

            # -------------------------------------------------
            # Load recording
            # -------------------------------------------------

            self.viewer.set_recording(
                recording
            )

            # -------------------------------------------------
            # Metadata
            # -------------------------------------------------

            self.info_label.setText(
                (
                    f"{recording.name}"
                    f"  •  "
                    f"{recording.channel_count} channels"
                    f"  •  "
                    f"{recording.sampling_frequency:.0f} Hz"
                    f"  •  "
                    f"{self._format_duration(recording.duration_seconds)}"
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Unable to open EEG",
                str(error),
            )

    # =========================================================
    # Processing Preview
    # =========================================================

    def apply_processing_preview(
        self,
        settings: ProcessingSettings,
    ):
        if self.recording is None:
            QMessageBox.warning(
                self,
                "No EEG loaded",
                (
                    "Open an EEG recording "
                    "before applying preprocessing."
                ),
            )

            return

        try:
            self.viewer.set_processing_settings(
                settings
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Processing failed",
                str(error),
            )

    # =========================================================
    # Candidate Detection
    # =========================================================

    def run_detection(
        self,
        thresholds: DetectionThresholds,
    ):
        if self.recording is None:
            QMessageBox.warning(
                self,
                "No EEG loaded",
                "Open an EEG recording first.",
            )

            return

        if (
            self.detection_worker
            is not None
            and self.detection_worker.isRunning()
        ):
            return

        # -----------------------------------------------------
        # Reset old results
        # -----------------------------------------------------

        self.viewer.set_artifact_candidates(
            []
        )

        self.review_panel.set_candidates(
            []
        )

        self.detection_panel.set_running(
            True
        )

        self.open_button.setEnabled(
            False
        )

        # -----------------------------------------------------
        # Background scan
        # -----------------------------------------------------

        self.detection_worker = (
            DetectionWorker(
                recording=self.recording,
                thresholds=thresholds,
            )
        )

        self.detection_worker.progress_changed.connect(
            self.detection_panel.set_progress
        )

        self.detection_worker.scan_completed.connect(
            self._detection_completed
        )

        self.detection_worker.scan_failed.connect(
            self._detection_failed
        )

        self.detection_worker.finished.connect(
            self._detection_worker_finished
        )

        self.detection_worker.start()

    # =========================================================
    # Detection results
    # =========================================================

    def _detection_completed(
        self,
        candidates: list,
    ):
        self.viewer.set_artifact_candidates(
            candidates
        )

        self.review_panel.set_candidates(
            candidates
        )

        self.detection_panel.set_complete(
            len(candidates)
        )

        if candidates:
            self.review_panel.list_widget.setCurrentRow(
                0
            )

    def _detection_failed(
        self,
        message: str,
    ):
        self.detection_panel.set_error(
            message
        )

        QMessageBox.critical(
            self,
            "Detection failed",
            message,
        )

    def _detection_worker_finished(
        self,
    ):
        self.open_button.setEnabled(
            True
        )

    # =========================================================
    # Review state
    # =========================================================

    def _candidate_updated(
        self,
        _candidate,
    ):
        self.viewer.render()

    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _format_duration(
        seconds: float,
    ) -> str:
        seconds = int(
            max(
                0,
                seconds,
            )
        )

        hours = (
            seconds // 3600
        )

        minutes = (
            seconds % 3600
        ) // 60

        remaining_seconds = (
            seconds % 60
        )

        if hours > 0:
            return (
                f"{hours}h "
                f"{minutes:02d}m "
                f"{remaining_seconds:02d}s"
            )

        return (
            f"{minutes}m "
            f"{remaining_seconds:02d}s"
        )