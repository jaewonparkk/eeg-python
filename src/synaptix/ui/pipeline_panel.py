from PySide6.QtCore import (
    Qt,
    Signal,
)

from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from synaptix.models.pipeline import (
    PipelineConfiguration,
)
from synaptix.processing.step_registry import (
    definition_for,
)


class PipelinePanel(QWidget):
    pipeline_changed = Signal(
        object
    )

    step_selected = Signal(
        object
    )

    def __init__(
        self,
        pipeline: PipelineConfiguration,
    ):
        super().__init__()

        self.pipeline = pipeline

        self.setMinimumWidth(
            250
        )

        self.setMaximumWidth(
            320
        )

        # =====================================================
        # Title
        # =====================================================

        title = QLabel(
            "Preprocessing Pipeline"
        )

        title.setStyleSheet(
            (
                "font-size: 18px;"
                "font-weight: 600;"
            )
        )

        subtitle = QLabel(
            (
                "Steps execute from top to "
                "bottom. Reordering changes "
                "the preprocessing result."
            )
        )

        subtitle.setWordWrap(
            True
        )

        # =====================================================
        # List
        # =====================================================

        self.list_widget = (
            QListWidget()
        )

        self.list_widget.itemChanged.connect(
            self._item_changed
        )

        self.list_widget.currentRowChanged.connect(
            self._selection_changed
        )

        # =====================================================
        # Move buttons
        # =====================================================

        self.up_button = QPushButton(
            "↑ Move Up"
        )

        self.down_button = QPushButton(
            "↓ Move Down"
        )

        self.up_button.clicked.connect(
            self._move_up
        )

        self.down_button.clicked.connect(
            self._move_down
        )

        button_layout = (
            QHBoxLayout()
        )

        button_layout.addWidget(
            self.up_button
        )

        button_layout.addWidget(
            self.down_button
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

        layout.addSpacing(
            10
        )

        layout.addWidget(
            self.list_widget,
            stretch=1,
        )

        layout.addLayout(
            button_layout
        )

        self.refresh()

    # =========================================================
    # Refresh
    # =========================================================

    def refresh(
        self,
        selected_step_id: str | None = None,
    ):
        if selected_step_id is None:
            current = (
                self.current_step()
            )

            if current is not None:
                selected_step_id = (
                    current.step_id
                )

        self.list_widget.blockSignals(
            True
        )

        self.list_widget.clear()

        selected_row = 0

        for index, step in enumerate(
            self.pipeline.steps
        ):
            definition = (
                definition_for(
                    step.step_type
                )
            )

            item = QListWidgetItem(
                (
                    f"{index + 1}. "
                    f"{definition.display_name}"
                )
            )

            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
            )

            item.setCheckState(
                (
                    Qt.CheckState.Checked
                    if step.enabled
                    else Qt.CheckState.Unchecked
                )
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                step.step_id,
            )

            self.list_widget.addItem(
                item
            )

            if (
                selected_step_id
                == step.step_id
            ):
                selected_row = index

        self.list_widget.setCurrentRow(
            selected_row
        )

        self.list_widget.blockSignals(
            False
        )

        self._selection_changed(
            selected_row
        )

    # =========================================================
    # Current step
    # =========================================================

    def current_step(
        self,
    ):
        row = (
            self.list_widget.currentRow()
        )

        if (
            row < 0
            or row
            >= len(
                self.pipeline.steps
            )
        ):
            return None

        return self.pipeline.steps[
            row
        ]

    # =========================================================
    # Enable / disable
    # =========================================================

    def _item_changed(
        self,
        item: QListWidgetItem,
    ):
        step_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        step = (
            self.pipeline.get_step(
                step_id
            )
        )

        if step is None:
            return

        step.enabled = (
            item.checkState()
            == Qt.CheckState.Checked
        )

        self.pipeline_changed.emit(
            self.pipeline
        )

    # =========================================================
    # Selection
    # =========================================================

    def _selection_changed(
        self,
        row: int,
    ):
        if (
            row < 0
            or row
            >= len(
                self.pipeline.steps
            )
        ):
            return

        self.step_selected.emit(
            self.pipeline.steps[
                row
            ]
        )

    # =========================================================
    # Move
    # =========================================================

    def _move_up(
        self,
    ):
        row = (
            self.list_widget.currentRow()
        )

        if row <= 0:
            return

        step = (
            self.pipeline.steps.pop(
                row
            )
        )

        self.pipeline.steps.insert(
            row - 1,
            step,
        )

        self.refresh(
            selected_step_id=(
                step.step_id
            )
        )

        self.pipeline_changed.emit(
            self.pipeline
        )

    def _move_down(
        self,
    ):
        row = (
            self.list_widget.currentRow()
        )

        if (
            row < 0
            or row
            >= len(
                self.pipeline.steps
            )
            - 1
        ):
            return

        step = (
            self.pipeline.steps.pop(
                row
            )
        )

        self.pipeline.steps.insert(
            row + 1,
            step,
        )

        self.refresh(
            selected_step_id=(
                step.step_id
            )
        )

        self.pipeline_changed.emit(
            self.pipeline
        )