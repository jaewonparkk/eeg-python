from PySide6.QtCore import (
    Qt,
)

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
from synaptix.models.pipeline import (
    PipelineConfiguration,
)
from synaptix.models.thresholds import (
    DetectionThresholds,
)
from synaptix.processing.script_generator import (
    generate_pipeline_script,
)
from synaptix.ui.detection_panel import (
    DetectionPanel,
)
from synaptix.ui.eeg_viewer import (
    EEGViewer,
)
from synaptix.ui.pipeline_panel import (
    PipelinePanel,
)
from synaptix.ui.review_panel import (
    ReviewPanel,
)
from synaptix.ui.script_preview import (
    ScriptPreviewPanel,
)
from synaptix.ui.step_inspector import (
    StepInspector,
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

        self.pipeline_config = (
            PipelineConfiguration.default()
        )

        # =====================================================
        # Window
        # =====================================================

        self.setWindowTitle(
            "Synaptix EEG Workbench"
        )

        self.resize(
            1700,
            1050,
        )

        # =====================================================
        # Top
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

        top_layout = QHBoxLayout()

        top_layout.addWidget(
            self.open_button
        )

        top_layout.addWidget(
            self.info_label,
            stretch=1,
        )

        # =====================================================
        # Pipeline
        # =====================================================

        self.pipeline_panel = (
            PipelinePanel(
                pipeline=(
                    self.pipeline_config
                )
            )
        )

        # =====================================================
        # Detection
        # =====================================================

        self.detection_panel = (
            DetectionPanel()
        )

        self.left_tabs = (
            QTabWidget()
        )

        self.left_tabs.addTab(
            self.pipeline_panel,
            "Pipeline",
        )

        self.left_tabs.addTab(
            self.detection_panel,
            "Detection",
        )

        self.left_tabs.setMinimumWidth(
            280
        )

        # =====================================================
        # Center viewer
        # =====================================================

        self.viewer = (
            EEGViewer()
        )

        self.viewer.set_pipeline_config(
            self.pipeline_config
        )

        # =====================================================
        # Right side
        # =====================================================

        self.step_inspector = (
            StepInspector()
        )

        self.review_panel = (
            ReviewPanel()
        )

        self.right_tabs = (
            QTabWidget()
        )

        self.right_tabs.addTab(
            self.step_inspector,
            "Step Details",
        )

        self.right_tabs.addTab(
            self.review_panel,
            "Review Queue",
        )

        self.right_tabs.setMinimumWidth(
            330
        )

        # =====================================================
        # Main horizontal workspace
        # =====================================================

        self.horizontal_splitter = (
            QSplitter(
                Qt.Orientation.Horizontal
            )
        )

        self.horizontal_splitter.addWidget(
            self.left_tabs
        )

        self.horizontal_splitter.addWidget(
            self.viewer
        )

        self.horizontal_splitter.addWidget(
            self.right_tabs
        )

        self.horizontal_splitter.setStretchFactor(
            0,
            0,
        )

        self.horizontal_splitter.setStretchFactor(
            1,
            1,
        )

        self.horizontal_splitter.setStretchFactor(
            2,
            0,
        )

        self.horizontal_splitter.setSizes(
            [
                290,
                1050,
                350,
            ]
        )

        # =====================================================
        # Script
        # =====================================================

        self.script_preview = (
            ScriptPreviewPanel()
        )

        self.vertical_splitter = (
            QSplitter(
                Qt.Orientation.Vertical
            )
        )

        self.vertical_splitter.addWidget(
            self.horizontal_splitter
        )

        self.vertical_splitter.addWidget(
            self.script_preview
        )

        self.vertical_splitter.setSizes(
            [
                780,
                250,
            ]
        )

        # =====================================================
        # Signals
        # =====================================================

        self.pipeline_panel.pipeline_changed.connect(
            self._pipeline_changed
        )

        self.pipeline_panel.step_selected.connect(
            self._step_selected
        )

        self.step_inspector.step_changed.connect(
            self._step_settings_changed
        )

        self.detection_panel.run_requested.connect(
            self.run_detection
        )

        self.review_panel.candidate_selected.connect(
            self.viewer.go_to_candidate
        )

        self.review_panel.candidate_updated.connect(
            self._candidate_updated
        )

        # =====================================================
        # Root
        # =====================================================

        root_layout = QVBoxLayout()

        root_layout.addLayout(
            top_layout
        )

        root_layout.addWidget(
            self.vertical_splitter,
            stretch=1,
        )

        container = QWidget()

        container.setLayout(
            root_layout
        )

        self.setCentralWidget(
            container
        )

        # =====================================================
        # Initial state
        # =====================================================

        self._update_script()

        if self.pipeline_config.steps:
            self.step_inspector.set_step(
                step=(
                    self.pipeline_config.steps[0]
                ),
                pipeline=(
                    self.pipeline_config
                ),
                recording=None,
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
                    "Wait for the current "
                    "candidate scan to finish."
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

            self.viewer.set_recording(
                recording
            )

            self.viewer.set_artifact_candidates(
                []
            )

            self.viewer.set_pipeline_config(
                self.pipeline_config
            )

            self.review_panel.set_candidates(
                []
            )

            self.info_label.setText(
                (
                    f"{recording.name}"
                    "  •  "
                    f"{recording.eeg_channel_count} "
                    "EEG channels"
                    "  •  "
                    f"{recording.sampling_frequency:.0f} Hz"
                    "  •  "
                    f"{self._format_duration(recording.duration_seconds)}"
                )
            )

            current_step = (
                self.pipeline_panel
                .current_step()
            )

            if current_step is not None:
                self.step_inspector.set_step(
                    step=current_step,
                    pipeline=(
                        self.pipeline_config
                    ),
                    recording=(
                        self.recording
                    ),
                )

            self._update_script()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Unable to open EEG",
                str(error),
            )

    # =========================================================
    # Pipeline
    # =========================================================

    def _pipeline_changed(
        self,
        pipeline: PipelineConfiguration,
    ):
        self.pipeline_config = (
            pipeline
        )

        self.viewer.set_pipeline_config(
            pipeline
        )

        current_step = (
            self.pipeline_panel
            .current_step()
        )

        if current_step is not None:
            self.step_inspector.set_step(
                step=current_step,
                pipeline=pipeline,
                recording=(
                    self.recording
                ),
            )

        self._update_script()

    def _step_selected(
        self,
        step,
    ):
        self.step_inspector.set_step(
            step=step,
            pipeline=(
                self.pipeline_config
            ),
            recording=(
                self.recording
            ),
        )

        self.right_tabs.setCurrentWidget(
            self.step_inspector
        )

    def _step_settings_changed(
        self,
        step,
    ):
        self.pipeline_panel.refresh(
            selected_step_id=(
                step.step_id
            )
        )

        self.viewer.set_pipeline_config(
            self.pipeline_config
        )

        self._update_script()

        self.step_inspector.set_step(
            step=step,
            pipeline=(
                self.pipeline_config
            ),
            recording=(
                self.recording
            ),
        )

    # =========================================================
    # Script
    # =========================================================

    def _update_script(
        self,
    ):
        path = (
            self.recording.source_path
            if self.recording
            is not None
            else None
        )

        script = (
            generate_pipeline_script(
                pipeline=(
                    self.pipeline_config
                ),
                input_path=path,
            )
        )

        self.script_preview.set_script(
            script
        )

    # =========================================================
    # Detection
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

        self.right_tabs.setCurrentWidget(
            self.review_panel
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

        remaining = (
            seconds % 60
        )

        if hours:
            return (
                f"{hours}h "
                f"{minutes:02d}m "
                f"{remaining:02d}s"
            )

        return (
            f"{minutes}m "
            f"{remaining:02d}s"
        )