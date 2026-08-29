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
from synaptix.models.bridge import (
    BridgeDetectionSettings,
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
from synaptix.processing.script_parser import (
    parse_bad_channels,
    parse_bridge_settings,
    parse_confirmed_bridges,
    parse_pipeline_script,
)
from synaptix.ui.bridge_panel import (
    BridgePanel,
)
from synaptix.ui.channel_quality_panel import (
    ChannelQualityPanel,
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
    BridgeDetectionWorker,
    ChannelQualityWorker,
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

        self.channel_quality_worker: (
            ChannelQualityWorker | None
        ) = None

        self.bridge_worker: (
            BridgeDetectionWorker | None
        ) = None

        self.pipeline_config = (
            PipelineConfiguration.default()
        )

        self.bridge_settings = (
            BridgeDetectionSettings()
        )

        # =====================================================
        # Window
        # =====================================================

        self.setWindowTitle(
            "Synaptix EEG Workbench"
        )

        self.resize(
            1800,
            1100,
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
            (
                "Open an EEG recording "
                "to begin."
            )
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
        # Left
        # =====================================================

        self.pipeline_panel = (
            PipelinePanel(
                pipeline=(
                    self.pipeline_config
                )
            )
        )

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
            "Artifacts",
        )

        self.left_tabs.setMinimumWidth(
            280
        )

        # =====================================================
        # Viewer
        # =====================================================

        self.viewer = (
            EEGViewer()
        )

        self.viewer.set_pipeline_config(
            self.pipeline_config
        )

        # =====================================================
        # Right
        # =====================================================

        self.step_inspector = (
            StepInspector()
        )

        self.channel_quality_panel = (
            ChannelQualityPanel()
        )

        self.bridge_panel = (
            BridgePanel()
        )

        self.bridge_panel.set_settings(
            self.bridge_settings
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
            self.channel_quality_panel,
            "Channel Quality",
        )

        self.right_tabs.addTab(
            self.bridge_panel,
            "Bridges",
        )

        self.right_tabs.addTab(
            self.review_panel,
            "Artifact Review",
        )

        self.right_tabs.setMinimumWidth(
            380
        )

        # =====================================================
        # Horizontal workspace
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
                1080,
                410,
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

        self.vertical_splitter.setStretchFactor(
            0,
            1,
        )

        self.vertical_splitter.setStretchFactor(
            1,
            0,
        )

        self.vertical_splitter.setSizes(
            [
                740,
                340,
            ]
        )

        # =====================================================
        # Signals - Pipeline
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

        # =====================================================
        # Signals - Script
        # =====================================================

        self.script_preview.apply_requested.connect(
            self._apply_script
        )

        self.script_preview.regenerate_requested.connect(
            self._regenerate_script
        )

        # =====================================================
        # Artifact detection
        # =====================================================

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
        # Channel quality
        # =====================================================

        self.channel_quality_panel.analyze_requested.connect(
            self.run_channel_quality
        )

        self.channel_quality_panel.mark_bad_requested.connect(
            self._mark_bad_channel
        )

        self.channel_quality_panel.keep_requested.connect(
            self._mark_good_channel
        )

        # =====================================================
        # Bridge detection
        # =====================================================

        self.bridge_panel.analyze_requested.connect(
            self.run_bridge_detection
        )

        self.bridge_panel.confirm_requested.connect(
            self._confirm_bridge
        )

        self.bridge_panel.reject_requested.connect(
            self._reject_bridge
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
        # Initial
        # =====================================================

        self._update_script()

        if self.pipeline_config.steps:
            self.step_inspector.set_step(
                step=(
                    self.pipeline_config.steps[
                        0
                    ]
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
        if self._worker_running():
            QMessageBox.warning(
                self,
                "Background task running",
                (
                    "Wait for the current "
                    "analysis to finish."
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

            self.channel_quality_panel.clear_results()

            self.bridge_panel.clear_results()

            self.channel_quality_panel.refresh_bad_states(
                recording.bad_channels
            )

            self._refresh_recording_status()

            self._refresh_step_inspector()

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
        self.pipeline_config = pipeline

        self.viewer.set_pipeline_config(
            pipeline
        )

        self._refresh_step_inspector()

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
    # Bridge Detection
    # =========================================================

    def run_bridge_detection(
        self,
        settings: BridgeDetectionSettings,
    ):
        if self.recording is None:
            QMessageBox.warning(
                self,
                "No EEG loaded",
                (
                    "Open an EEG recording "
                    "before detecting bridges."
                ),
            )

            return

        if self._worker_running():
            return

        self.bridge_settings = (
            settings
        )

        if not settings.enabled:
            self.bridge_panel.set_results(
                []
            )

            self._update_script()

            return

        self.bridge_panel.set_running(
            True
        )

        self.open_button.setEnabled(
            False
        )

        self.bridge_worker = (
            BridgeDetectionWorker(
                recording=(
                    self.recording
                ),
                settings=(
                    settings
                ),
            )
        )

        self.bridge_worker.analysis_completed.connect(
            self._bridge_detection_completed
        )

        self.bridge_worker.analysis_failed.connect(
            self._bridge_detection_failed
        )

        self.bridge_worker.finished.connect(
            self._background_worker_finished
        )

        self.bridge_worker.start()

        self._update_script()

    def _bridge_detection_completed(
        self,
        candidates: list,
    ):
        if self.recording is not None:
            confirmed = {
                frozenset(
                    pair
                )
                for pair
                in self.recording
                .confirmed_bridge_pairs
            }

            for candidate in candidates:
                pair = frozenset(
                    (
                        candidate.channel_a,
                        candidate.channel_b,
                    )
                )

                if pair in confirmed:
                    candidate.confirmed = (
                        True
                    )

        self.bridge_panel.set_results(
            candidates
        )

        self.right_tabs.setCurrentWidget(
            self.bridge_panel
        )

    def _bridge_detection_failed(
        self,
        message: str,
    ):
        self.bridge_panel.set_error(
            message
        )

        QMessageBox.critical(
            self,
            "Bridge detection failed",
            message,
        )

    def _confirm_bridge(
        self,
        candidate,
    ):
        if self.recording is None:
            return

        self.recording.confirm_bridge_pair(
            candidate.channel_a,
            candidate.channel_b,
        )

        candidate.confirmed = True

        self.bridge_panel.sync_confirmed_pairs(
            self.recording
            .confirmed_bridge_pairs
        )

        self._bridge_state_changed()

    def _reject_bridge(
        self,
        candidate,
    ):
        if self.recording is None:
            return

        self.recording.clear_bridge_pair(
            candidate.channel_a,
            candidate.channel_b,
        )

        candidate.confirmed = False

        self.bridge_panel._populate_list(
            selected_pair=(
                candidate.channel_a,
                candidate.channel_b,
            )
        )

        self._bridge_state_changed()

    def _bridge_state_changed(
        self,
    ):
        self._refresh_step_inspector()

        self._refresh_recording_status()

        self._update_script()

    # =========================================================
    # Channel Quality
    # =========================================================

    def run_channel_quality(
        self,
        thresholds,
    ):
        if self.recording is None:
            QMessageBox.warning(
                self,
                "No EEG loaded",
                (
                    "Open an EEG recording "
                    "before analyzing "
                    "channel quality."
                ),
            )

            return

        if self._worker_running():
            return

        self.channel_quality_panel.set_running(
            True
        )

        self.open_button.setEnabled(
            False
        )

        self.channel_quality_worker = (
            ChannelQualityWorker(
                recording=(
                    self.recording
                ),
                thresholds=(
                    thresholds
                ),
            )
        )

        self.channel_quality_worker.progress_changed.connect(
            self.channel_quality_panel.set_progress
        )

        self.channel_quality_worker.analysis_completed.connect(
            self._channel_quality_completed
        )

        self.channel_quality_worker.analysis_failed.connect(
            self._channel_quality_failed
        )

        self.channel_quality_worker.finished.connect(
            self._background_worker_finished
        )

        self.channel_quality_worker.start()

    def _channel_quality_completed(
        self,
        results: list,
    ):
        self.channel_quality_panel.set_results(
            results
        )

        if self.recording is not None:
            self.channel_quality_panel.refresh_bad_states(
                self.recording.bad_channels
            )

        self.right_tabs.setCurrentWidget(
            self.channel_quality_panel
        )

    def _channel_quality_failed(
        self,
        message: str,
    ):
        self.channel_quality_panel.set_error(
            message
        )

        QMessageBox.critical(
            self,
            "Channel analysis failed",
            message,
        )

    def _mark_bad_channel(
        self,
        channel: str,
    ):
        if self.recording is None:
            return

        self.recording.mark_bad_channel(
            channel
        )

        self._bad_channel_state_changed()

    def _mark_good_channel(
        self,
        channel: str,
    ):
        if self.recording is None:
            return

        self.recording.mark_good_channel(
            channel
        )

        self._bad_channel_state_changed()

    def _bad_channel_state_changed(
        self,
    ):
        if self.recording is None:
            return

        self.channel_quality_panel.refresh_bad_states(
            self.recording.bad_channels
        )

        self.viewer.set_pipeline_config(
            self.pipeline_config
        )

        self._refresh_step_inspector()

        self._refresh_recording_status()

        self._update_script()

    # =========================================================
    # Artifact Detection
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

        if self._worker_running():
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
                recording=(
                    self.recording
                ),
                thresholds=(
                    thresholds
                ),
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
            self._background_worker_finished
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

    def _candidate_updated(
        self,
        _candidate,
    ):
        self.viewer.render()

    # =========================================================
    # Script
    # =========================================================

    def _apply_script(
        self,
        script: str,
    ):
        try:
            parsed_pipeline = (
                parse_pipeline_script(
                    script=script,
                    current_pipeline=(
                        self.pipeline_config
                    ),
                )
            )

            parsed_bad_channels = (
                parse_bad_channels(
                    script
                )
            )

            parsed_bridge_settings = (
                parse_bridge_settings(
                    script=script,
                    current_settings=(
                        self.bridge_settings
                    ),
                )
            )

            parsed_bridges = (
                parse_confirmed_bridges(
                    script
                )
            )

            if self.recording is None:
                if parsed_bad_channels:
                    raise ValueError(
                        (
                            "Open an EEG before "
                            "applying BAD_CHANNELS."
                        )
                    )

                if parsed_bridges:
                    raise ValueError(
                        (
                            "Open an EEG before "
                            "applying CONFIRMED_BRIDGES."
                        )
                    )

            else:
                if (
                    parsed_bad_channels
                    is not None
                ):
                    self.recording.set_bad_channels(
                        parsed_bad_channels
                    )

                if parsed_bridges is not None:
                    self.recording.set_confirmed_bridge_pairs(
                        parsed_bridges
                    )

        except ValueError as error:
            self.script_preview.set_status(
                (
                    "Script configuration error:\n"
                    f"{error}"
                )
            )

            return

        self.pipeline_config = (
            parsed_pipeline
        )

        self.bridge_settings = (
            parsed_bridge_settings
        )

        self.pipeline_panel.set_pipeline(
            parsed_pipeline
        )

        self.bridge_panel.set_settings(
            parsed_bridge_settings
        )

        self.viewer.set_pipeline_config(
            parsed_pipeline
        )

        if self.recording is not None:
            self.channel_quality_panel.refresh_bad_states(
                self.recording.bad_channels
            )

            self.bridge_panel.sync_confirmed_pairs(
                self.recording
                .confirmed_bridge_pairs
            )

        self._refresh_step_inspector()

        self._refresh_recording_status()

        self.script_preview.set_status(
            (
                "✓ Script settings applied "
                "to pipeline, channel state, "
                "and bridge state."
            )
        )

    def _regenerate_script(
        self,
    ):
        self._update_script()

        self.script_preview.set_status(
            (
                "✓ Script regenerated "
                "from current Synaptix state."
            )
        )

    def _update_script(
        self,
    ):
        if self.recording is None:
            path = None

            bad_channels = []

            confirmed_bridges = []

        else:
            path = (
                self.recording
                .source_path
            )

            bad_channels = (
                self.recording
                .bad_channels
            )

            confirmed_bridges = (
                self.recording
                .confirmed_bridge_pairs
            )

        script = (
            generate_pipeline_script(
                pipeline=(
                    self.pipeline_config
                ),
                input_path=path,
                bad_channels=(
                    bad_channels
                ),
                bridge_settings=(
                    self.bridge_settings
                ),
                confirmed_bridges=(
                    confirmed_bridges
                ),
            )
        )

        self.script_preview.set_script(
            script
        )

    # =========================================================
    # General helpers
    # =========================================================

    def _worker_running(
        self,
    ) -> bool:
        workers = [
            self.detection_worker,
            self.channel_quality_worker,
            self.bridge_worker,
        ]

        return any(
            (
                worker is not None
                and worker.isRunning()
            )
            for worker
            in workers
        )

    def _background_worker_finished(
        self,
    ):
        self.open_button.setEnabled(
            True
        )

    def _refresh_step_inspector(
        self,
    ):
        current_step = (
            self.pipeline_panel
            .current_step()
        )

        if current_step is None:
            return

        self.step_inspector.set_step(
            step=current_step,
            pipeline=(
                self.pipeline_config
            ),
            recording=(
                self.recording
            ),
        )

    def _refresh_recording_status(
        self,
    ):
        if self.recording is None:
            return

        self.info_label.setText(
            (
                f"{self.recording.name}"
                "  •  "
                f"{self.recording.eeg_channel_count} "
                "EEG channels"
                "  •  "
                f"{self.recording.sampling_frequency:.0f} Hz"
                "  •  "
                f"{self._format_duration(self.recording.duration_seconds)}"
                "  •  "
                f"{len(self.recording.bad_channels)} bad"
                "  •  "
                f"{len(self.recording.confirmed_bridge_pairs)} "
                "confirmed bridge(s)"
            )
        )

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
            seconds
            // 3600
        )

        minutes = (
            seconds
            % 3600
        ) // 60

        remaining = (
            seconds
            % 60
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