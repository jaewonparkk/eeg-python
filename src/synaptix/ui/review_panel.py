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
    candidate_selected = Signal(object)

    def __init__(self):
        super().__init__()

        self.setMaximumWidth(300)

        self.candidates: list[
            ArtifactCandidate
        ] = []

        self.current_candidate: (
            ArtifactCandidate | None
        ) = None

        title = QLabel(
            "Review Queue"
        )

        title.setStyleSheet(
            "font-size: 18px; "
            "font-weight: 600;"
        )

        self.summary_label = QLabel(
            "No detection results"
        )

        self.list_widget = QListWidget()

        self.list_widget.currentRowChanged.connect(
            self._candidate_changed
        )

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

        self.accept_button = QPushButton(
            "Accept"
        )

        self.reject_button = QPushButton(
            "Reject"
        )

        self.accept_button.clicked.connect(
            self._accept_current
        )

        self.reject_button.clicked.connect(
            self._reject_current
        )

        self.accept_button.setEnabled(False)
        self.reject_button.setEnabled(False)

        layout = QVBoxLayout(self)

        layout.addWidget(title)
        layout.addWidget(
            self.summary_label
        )

        layout.addSpacing(10)

        layout.addWidget(
            self.list_widget,
            stretch=1,
        )

        layout.addSpacing(15)

        layout.addWidget(
            why_title
        )

        layout.addWidget(
            self.reason_label
        )

        layout.addSpacing(15)

        layout.addWidget(
            self.reject_button
        )

        layout.addWidget(
            self.accept_button
        )

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

        self.list_widget.clear()

        for candidate in self.candidates:
            self.list_widget.addItem(
                self._candidate_text(
                    candidate
                )
            )

        self.summary_label.setText(
            f"{len(self.candidates)} candidates"
        )

        self.current_candidate = None

        self.reason_label.setText(
            "Select a candidate."
        )

        self.accept_button.setEnabled(False)
        self.reject_button.setEnabled(False)

    def _candidate_changed(
        self,
        index: int,
    ):
        if (
            index < 0
            or index >= len(self.candidates)
        ):
            return

        candidate = self.candidates[
            index
        ]

        self.current_candidate = candidate

        self.reason_label.setText(
            candidate.reason
        )

        self.accept_button.setEnabled(True)
        self.reject_button.setEnabled(True)

        self.candidate_selected.emit(
            candidate
        )

    def _accept_current(self):
        if self.current_candidate is None:
            return

        self.current_candidate.accepted = True

        self._refresh_current_item()

    def _reject_current(self):
        if self.current_candidate is None:
            return

        self.current_candidate.accepted = False

        self._refresh_current_item()

    def _refresh_current_item(self):
        row = self.list_widget.currentRow()

        if row < 0:
            return

        item = self.list_widget.item(row)

        item.setText(
            self._candidate_text(
                self.current_candidate
            )
        )

        self._update_summary()

    def _update_summary(self):
        accepted = sum(
            candidate.accepted is True
            for candidate in self.candidates
        )

        rejected = sum(
            candidate.accepted is False
            for candidate in self.candidates
        )

        remaining = (
            len(self.candidates)
            - accepted
            - rejected
        )

        self.summary_label.setText(
            f"{remaining} remaining • "
            f"{accepted} accepted • "
            f"{rejected} rejected"
        )

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

        return (
            f"{status} "
            f"{candidate.start_seconds:07.2f}s "
            f"• {channel} "
            f"• {candidate.artifact_type.value}"
        )