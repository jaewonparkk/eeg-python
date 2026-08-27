import ast
import copy

from synaptix.models.pipeline import (
    PipelineConfiguration,
)


SUPPORTED_SETTINGS = {
    "PIPELINE_ORDER",
    "BANDPASS_ENABLED",
    "HIGHPASS_HZ",
    "LOWPASS_HZ",
    "FILTER_ORDER",
    "NOTCH_ENABLED",
    "NOTCH_HZ",
    "NOTCH_Q",
    "AVERAGE_REFERENCE_ENABLED",
    "REFERENCE_EXCLUDE",
}


EXPECTED_STEP_IDS = {
    "bandpass",
    "notch",
    "average_reference",
}


def parse_pipeline_script(
    script: str,
    current_pipeline: PipelineConfiguration,
) -> PipelineConfiguration:
    """
    Parse Synaptix configuration values from an editable
    Python script.

    IMPORTANT:
    The script is never executed.

    Only whitelisted top-level constant assignments are
    extracted using Python's AST + ast.literal_eval.
    """

    try:
        tree = ast.parse(
            script
        )

    except SyntaxError as error:
        raise ValueError(
            (
                "The script contains invalid Python syntax.\n"
                f"Line {error.lineno}: {error.msg}"
            )
        ) from error

    values: dict[
        str,
        object,
    ] = {}

    # =========================================================
    # Extract whitelisted assignments
    # =========================================================

    for node in tree.body:
        if not isinstance(
            node,
            ast.Assign,
        ):
            continue

        if len(node.targets) != 1:
            continue

        target = node.targets[0]

        if not isinstance(
            target,
            ast.Name,
        ):
            continue

        name = target.id

        if name not in SUPPORTED_SETTINGS:
            continue

        try:
            value = ast.literal_eval(
                node.value
            )

        except (
            ValueError,
            TypeError,
        ) as error:
            raise ValueError(
                (
                    f"{name} must be a literal value "
                    "such as a number, boolean, string, "
                    "or list."
                )
            ) from error

        values[
            name
        ] = value

    # =========================================================
    # Copy existing pipeline
    # =========================================================

    pipeline = copy.deepcopy(
        current_pipeline
    )

    bandpass = pipeline.get_step(
        "bandpass"
    )

    notch = pipeline.get_step(
        "notch"
    )

    reference = pipeline.get_step(
        "average_reference"
    )

    if (
        bandpass is None
        or notch is None
        or reference is None
    ):
        raise ValueError(
            (
                "The current pipeline is missing "
                "one or more required Synaptix steps."
            )
        )

    # =========================================================
    # Pipeline order
    # =========================================================

    if "PIPELINE_ORDER" in values:
        order = values[
            "PIPELINE_ORDER"
        ]

        if not isinstance(
            order,
            list,
        ):
            raise ValueError(
                "PIPELINE_ORDER must be a list."
            )

        if not all(
            isinstance(
                item,
                str,
            )
            for item in order
        ):
            raise ValueError(
                (
                    "Every PIPELINE_ORDER item "
                    "must be a string."
                )
            )

        if len(order) != len(
            EXPECTED_STEP_IDS
        ):
            raise ValueError(
                (
                    "PIPELINE_ORDER must contain "
                    "bandpass, notch, and "
                    "average_reference exactly once."
                )
            )

        if set(order) != (
            EXPECTED_STEP_IDS
        ):
            raise ValueError(
                (
                    "PIPELINE_ORDER must contain exactly:\n"
                    "bandpass\n"
                    "notch\n"
                    "average_reference"
                )
            )

        step_map = {
            step.step_id: step
            for step in pipeline.steps
        }

        pipeline.steps = [
            step_map[
                step_id
            ]
            for step_id in order
        ]

    # =========================================================
    # Band-pass
    # =========================================================

    if "BANDPASS_ENABLED" in values:
        bandpass.enabled = _require_bool(
            "BANDPASS_ENABLED",
            values["BANDPASS_ENABLED"],
        )

    if "HIGHPASS_HZ" in values:
        bandpass.parameters[
            "highpass_hz"
        ] = _require_positive_number(
            "HIGHPASS_HZ",
            values["HIGHPASS_HZ"],
        )

    if "LOWPASS_HZ" in values:
        bandpass.parameters[
            "lowpass_hz"
        ] = _require_positive_number(
            "LOWPASS_HZ",
            values["LOWPASS_HZ"],
        )

    if "FILTER_ORDER" in values:
        order_value = values[
            "FILTER_ORDER"
        ]

        if (
            not isinstance(
                order_value,
                int,
            )
            or isinstance(
                order_value,
                bool,
            )
            or order_value < 1
            or order_value > 10
        ):
            raise ValueError(
                (
                    "FILTER_ORDER must be an "
                    "integer from 1 to 10."
                )
            )

        bandpass.parameters[
            "order"
        ] = order_value

    highpass = float(
        bandpass.parameters.get(
            "highpass_hz",
            0.5,
        )
    )

    lowpass = float(
        bandpass.parameters.get(
            "lowpass_hz",
            45.0,
        )
    )

    if lowpass <= highpass:
        raise ValueError(
            (
                "LOWPASS_HZ must be greater "
                "than HIGHPASS_HZ."
            )
        )

    # =========================================================
    # Notch
    # =========================================================

    if "NOTCH_ENABLED" in values:
        notch.enabled = _require_bool(
            "NOTCH_ENABLED",
            values["NOTCH_ENABLED"],
        )

    if "NOTCH_HZ" in values:
        notch.parameters[
            "frequency_hz"
        ] = _require_positive_number(
            "NOTCH_HZ",
            values["NOTCH_HZ"],
        )

    if "NOTCH_Q" in values:
        notch.parameters[
            "quality_factor"
        ] = _require_positive_number(
            "NOTCH_Q",
            values["NOTCH_Q"],
        )

    # =========================================================
    # Average reference
    # =========================================================

    if (
        "AVERAGE_REFERENCE_ENABLED"
        in values
    ):
        reference.enabled = _require_bool(
            "AVERAGE_REFERENCE_ENABLED",
            values[
                "AVERAGE_REFERENCE_ENABLED"
            ],
        )

    if "REFERENCE_EXCLUDE" in values:
        excluded = values[
            "REFERENCE_EXCLUDE"
        ]

        if not isinstance(
            excluded,
            list,
        ):
            raise ValueError(
                (
                    "REFERENCE_EXCLUDE must "
                    "be a list of channel names."
                )
            )

        if not all(
            isinstance(
                channel,
                str,
            )
            for channel in excluded
        ):
            raise ValueError(
                (
                    "Every REFERENCE_EXCLUDE "
                    "item must be a string."
                )
            )

        reference.parameters[
            "exclude_channels"
        ] = excluded

    return pipeline


def _require_bool(
    name: str,
    value: object,
) -> bool:
    if not isinstance(
        value,
        bool,
    ):
        raise ValueError(
            f"{name} must be True or False."
        )

    return value


def _require_positive_number(
    name: str,
    value: object,
) -> float:
    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            (
                int,
                float,
            ),
        )
    ):
        raise ValueError(
            f"{name} must be a number."
        )

    number = float(
        value
    )

    if number <= 0:
        raise ValueError(
            (
                f"{name} must be "
                "greater than 0."
            )
        )

    return number