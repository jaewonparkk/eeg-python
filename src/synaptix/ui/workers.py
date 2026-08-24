from PySide6.QtCore import QThread, Signal

from synaptix.core.recording import Recording
from synaptix.detection.artifact_detector import (
    ArtifactDetector,
)
from synaptix.models.thresholds import (
    DetectionThresholds,
)


class DetectionWorker(QThread):
    progress_changed = Signal(int)
    scan_completed = Signal(list)
    scan_failed = Signal(str)

    def __init__(
        self,
        recording: Recording,
        thresholds: DetectionThresholds,
    ):
        super().__init__()

        self.recording = recording
        self.thresholds = thresholds

    def run(self):
        try:
            detector = ArtifactDetector(
                thresholds=self.thresholds
            )

            candidates = detector.detect_recording(
                recording=self.recording,
                chunk_seconds=30.0,
                progress_callback=(
                    self.progress_changed.emit
                ),
            )

            self.scan_completed.emit(
                candidates
            )

        except Exception as error:
            self.scan_failed.emit(
                str(error)
            )