from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


class StepType(str, Enum):
    BANDPASS = "bandpass"
    NOTCH = "notch"
    AVERAGE_REFERENCE = (
        "average_reference"
    )


class PipelineStep(BaseModel):
    step_id: str

    step_type: StepType

    enabled: bool = True

    parameters: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )


class PipelineConfiguration(BaseModel):
    steps: list[
        PipelineStep
    ] = Field(
        default_factory=list
    )

    preview_padding_seconds: float = (
        2.0
    )

    # =========================================================
    # Defaults
    # =========================================================

    @classmethod
    def default(
        cls,
    ) -> "PipelineConfiguration":
        return cls(
            steps=[
                PipelineStep(
                    step_id="bandpass",
                    step_type=(
                        StepType.BANDPASS
                    ),
                    enabled=True,
                    parameters={
                        "highpass_hz": 0.5,
                        "lowpass_hz": 45.0,
                        "order": 4,
                    },
                ),
                PipelineStep(
                    step_id="notch",
                    step_type=(
                        StepType.NOTCH
                    ),
                    enabled=False,
                    parameters={
                        "frequency_hz": 60.0,
                        "quality_factor": 30.0,
                    },
                ),
                PipelineStep(
                    step_id=(
                        "average_reference"
                    ),
                    step_type=(
                        StepType.AVERAGE_REFERENCE
                    ),
                    enabled=False,
                    parameters={
                        "exclude_channels": [],
                    },
                ),
            ]
        )

    # =========================================================
    # Helpers
    # =========================================================

    def get_step(
        self,
        step_id: str,
    ) -> PipelineStep | None:
        for step in self.steps:
            if step.step_id == step_id:
                return step

        return None

    def enabled_steps(
        self,
    ) -> list[PipelineStep]:
        return [
            step
            for step in self.steps
            if step.enabled
        ]