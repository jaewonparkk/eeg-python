from dataclasses import dataclass

from synaptix.models.pipeline import (
    StepType,
)


@dataclass(
    frozen=True,
    slots=True,
)
class StepDefinition:
    display_name: str

    description: str

    preview_function: str

    export_function: str

    input_type: str


STEP_DEFINITIONS = {
    StepType.BANDPASS: StepDefinition(
        display_name=(
            "Band-pass Filter"
        ),
        description=(
            "Retains EEG activity inside "
            "the configured frequency range "
            "while attenuating frequencies "
            "outside that range."
        ),
        preview_function=(
            "scipy.signal.sosfiltfilt"
        ),
        export_function=(
            "raw.filter"
        ),
        input_type=(
            "Continuous EEG"
        ),
    ),

    StepType.NOTCH: StepDefinition(
        display_name=(
            "Notch Filter"
        ),
        description=(
            "Attenuates a narrow frequency "
            "band, typically used for "
            "power-line contamination."
        ),
        preview_function=(
            "scipy.signal.filtfilt"
        ),
        export_function=(
            "raw.notch_filter"
        ),
        input_type=(
            "Continuous EEG"
        ),
    ),

    StepType.AVERAGE_REFERENCE: (
        StepDefinition(
            display_name=(
                "Average Reference"
            ),
            description=(
                "Computes a reference signal "
                "from the average of eligible "
                "EEG channels and subtracts "
                "that reference from each EEG "
                "channel."
            ),
            preview_function=(
                "average_reference"
            ),
            export_function=(
                "raw.set_eeg_reference"
            ),
            input_type=(
                "Continuous EEG"
            ),
        )
    ),
}


def definition_for(
    step_type: StepType,
) -> StepDefinition:
    return STEP_DEFINITIONS[
        step_type
    ]