from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from synaptix.models.artifact import (
    ArtifactCandidate,
)


class ReviewPanel(QWidget):
    candidate_selected = Signal(
        object
    )

    candidate_updated = Signal(
        object
    )

    def __init__(self):
        super().__init__()

        self.setMinimumWidth(
            280
        )

        self.setMaximumWidth(
            340
        )

        self.candidates: list[
            ArtifactCandidate
        ] = []

        self.current_candidate: (
            ArtifactCandidate | None
        ) = None

        # =====================================================
        # Title
        # =====================================================

        title = QLabel(
            "Review Queue"
        )

        title.setStyleSheet(
            "font-size: 18px;"
            "font-weight: 600;"
        )

        self.summary_label = QLabel(
            "No detection results"
        )

        # =====================================================
        # Candidate list
        # =====================================================

        self.list_widget = QListWidget()

        self.list_widget.currentRowChanged.connect(
            self._candidate_changed
        )

        # =====================================================
        # Details
        # =====================================================

        details_title = QLabel(
            "Candidate Details"
        )

        details_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.type_label = QLabel(
            "Type: —"
        )

        self.channel_label = QLabel(
            "Channel: —"
        )

        self.time_label = QLabel(
            "Time: —"
        )

        self.metric_label = QLabel(
            "Metric: —"
        )

        # =====================================================
        # Reason
        # =====================================================

        why_title = QLabel(
            "Why was this flagged?"
        )

        why_title.setStyleSheet(
            "font-weight: 600;"
        )

        self.reason_label = QLabel(
            "Select a candidate."
        )

        self.reason_label.setWordWrap(
            True
        )

        # =====================================================
        # Review buttons
        # =====================================================

        self.accept_button = QPushButton(
            "Accept Candidate"
        )

        self.reject_button = QPushButton(
            "Reject Candidate"
        )

        self.accept_button.clicked.connect(
            self._accept_current
        )

        self.reject_button.clicked.connect(
            self._reject_current
        )

        self.accept_button.setEnabled(
            False
        )

        self.reject_button.setEnabled(
            False
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
            self.summary_label
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            self.list_widget,
            stretch=1,
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            details_title
        )

        layout.addWidget(
            self.type_label
        )

        layout.addWidget(
            self.channel_label
        )

        layout.addWidget(
            self.time_label
        )

        layout.addWidget(
            self.metric_label
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            why_title
        )

        layout.addWidget(
            self.reason_label
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            self.reject_button
        )

        layout.addWidget(
            self.accept_button
        )

    # =========================================================
    # Set Candidates
    # =========================================================

    def set_candidates(
        self,
        candidates: list[
            ArtifactCandidate
        ],
    ):
        self.candidates = sorted(
            candidates,
            key=lambda candidate: (
                candidate.start_seconds
            ),
        )

        self.current_candidate = None

        self.list_widget.clear()

        for candidate in self.candidates:
            self.list_widget.addItem(
                self._candidate_text(
                    candidate
                )
            )

        self._update_summary()

        self.type_label.setText(
            "Type: —"
        )

        self.channel_label.setText(
            "Channel: —"
        )

        self.time_label.setText(
            "Time: —"
        )

        self.metric_label.setText(
            "Metric: —"
        )

        self.reason_label.setText(
            "Select a candidate."
        )

        self.accept_button.setEnabled(
            False
        )

        self.reject_button.setEnabled(
            False
        )

    # =========================================================
    # Selection
    # =========================================================

    def _candidate_changed(
        self,
        index: int,
    ):
        if (
            index < 0
            or index >= len(
                self.candidates
            )
        ):
            return

        candidate = self.candidates[
            index
        ]

        self.current_candidate = (
            candidate
        )

        artifact_name = (
            candidate.artifact_type.value
            .replace(
                "_",
                " ",
            )
            .title()
        )

        self.type_label.setText(
            f"Type: {artifact_name}"
        )

        channels = (
            ", ".join(
                candidate.channels
            )
            if candidate.channels
            else "Unknown"
        )

        self.channel_label.setText(
            f"Channel: {channels}"
        )

        self.time_label.setText(
            (
                f"Time: "
                f"{candidate.start_seconds:.2f}s"
                f" – "
                f"{candidate.end_seconds:.2f}s"
            )
        )

        if (
            candidate.measured_value
            is not None
        ):
            metric_name = (
                candidate.metric_name
                or "Measured"
            )

            unit = (
                candidate.unit
                or ""
            )

            self.metric_label.setText(
                (
                    f"{metric_name}: "
                    f"{candidate.measured_value:.2f}"
                    f" {unit}"
                )
            )

        else:
            self.metric_label.setText(
                "Metric: —"
            )

        self.reason_label.setText(
            candidate.reason
        )

        self.accept_button.setEnabled(
            True
        )

        self.reject_button.setEnabled(
            True
        )

        self.candidate_selected.emit(
            candidate
        )

    # =========================================================
    # Review Decisions
    # =========================================================

    def _accept_current(
        self,
    ):
        if self.current_candidate is None:
            return

        self.current_candidate.accepted = True

        self._refresh_current_item()

        self.candidate_updated.emit(
            self.current_candidate
        )

    def _reject_current(
        self,
    ):
        if self.current_candidate is None:
            return

        self.current_candidate.accepted = False

        self._refresh_current_item()

        self.candidate_updated.emit(
            self.current_candidate
        )

    def _refresh_current_item(
        self,
    ):
        row = (
            self.list_widget.currentRow()
        )

        if row < 0:
            return

        item = (
            self.list_widget.item(
                row
            )
        )

        item.setText(
            self._candidate_text(
                self.current_candidate
            )
        )

        self._update_summary()

    # =========================================================
    # Summary
    # =========================================================

    def _update_summary(
        self,
    ):
        total = len(
            self.candidates
        )

        accepted = sum(
            candidate.accepted is True
            for candidate in self.candidates
        )

        rejected = sum(
            candidate.accepted is False
            for candidate in self.candidates
        )

        remaining = (
            total
            - accepted
            - rejected
        )

        if total == 0:
            self.summary_label.setText(
                "No detection results"
            )

            return

        self.summary_label.setText(
            (
                f"{remaining} remaining"
                f" • "
                f"{accepted} accepted"
                f" • "
                f"{rejected} rejected"
            )
        )

    # =========================================================
    # Display
    # =========================================================

    @staticmethod
    def _candidate_text(
        candidate: ArtifactCandidate,
    ) -> str:
        status = "○"

        if candidate.accepted is True:
            status = "✓"

        elif candidate.accepted is False:
            status = "×"

        channel = (
            candidate.channels[0]
            if candidate.channels
            else "Unknown"
        )

        artifact_name = (
            candidate.artifact_type.value
            .replace(
                "_",
                " ",
            )
            .title()
        )

        return (
            f"{status} "
            f"{candidate.start_seconds:07.2f}s "
            f"• {channel} "
            f"• {artifact_name}"
        )