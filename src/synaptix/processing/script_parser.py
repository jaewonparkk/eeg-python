import ast
import copy

from synaptix.models.pipeline import (
    PipelineConfiguration,
)


SUPPORTED_SETTINGS = {
    "PIPELINE_ORDER",
    "BAD_CHANNELS",
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


def _extract_values(
    script: str,
) -> dict[
    str,
    object,
]:
    try:
        tree = ast.parse(
            script
        )

    except SyntaxError as error:
        raise ValueError(
            (
                "The script contains invalid "
                "Python syntax.\n"
                f"Line {error.lineno}: "
                f"{error.msg}"
            )
        ) from error

    values: dict[
        str,
        object,
    ] = {}

    for node in tree.body:
        if not isinstance(
            node,
            ast.Assign,
        ):
            continue

        if len(
            node.targets
        ) != 1:
            continue

        target = (
            node.targets[
                0
            ]
        )

        if not isinstance(
            target,
            ast.Name,
        ):
            continue

        name = target.id

        if (
            name
            not in SUPPORTED_SETTINGS
        ):
            continue

        try:
            value = (
                ast.literal_eval(
                    node.value
                )
            )

        except (
            ValueError,
            TypeError,
        ) as error:
            raise ValueError(
                (
                    f"{name} must use a "
                    "literal configuration value."
                )
            ) from error

        values[
            name
        ] = value

    return values


def parse_bad_channels(
    script: str,
) -> list[str] | None:
    values = (
        _extract_values(
            script
        )
    )

    if (
        "BAD_CHANNELS"
        not in values
    ):
        return None

    bad_channels = (
        values[
            "BAD_CHANNELS"
        ]
    )

    if not isinstance(
        bad_channels,
        list,
    ):
        raise ValueError(
            (
                "BAD_CHANNELS must "
                "be a list."
            )
        )

    if not all(
        isinstance(
            channel,
            str,
        )
        for channel
        in bad_channels
    ):
        raise ValueError(
            (
                "Every BAD_CHANNELS item "
                "must be a channel-name string."
            )
        )

    if len(
        bad_channels
    ) != len(
        set(
            bad_channels
        )
    ):
        raise ValueError(
            (
                "BAD_CHANNELS cannot "
                "contain duplicate channels."
            )
        )

    return list(
        bad_channels
    )


def parse_pipeline_script(
    script: str,
    current_pipeline: PipelineConfiguration,
) -> PipelineConfiguration:
    values = (
        _extract_values(
            script
        )
    )

    pipeline = (
        copy.deepcopy(
            current_pipeline
        )
    )

    bandpass = (
        pipeline.get_step(
            "bandpass"
        )
    )

    notch = (
        pipeline.get_step(
            "notch"
        )
    )

    reference = (
        pipeline.get_step(
            "average_reference"
        )
    )

    if (
        bandpass is None
        or notch is None
        or reference is None
    ):
        raise ValueError(
            (
                "The current pipeline "
                "is missing required "
                "Synaptix steps."
            )
        )

    # =========================================================
    # Order
    # =========================================================

    if (
        "PIPELINE_ORDER"
        in values
    ):
        order = (
            values[
                "PIPELINE_ORDER"
            ]
        )

        if not isinstance(
            order,
            list,
        ):
            raise ValueError(
                (
                    "PIPELINE_ORDER "
                    "must be a list."
                )
            )

        if not all(
            isinstance(
                item,
                str,
            )
            for item
            in order
        ):
            raise ValueError(
                (
                    "Every PIPELINE_ORDER "
                    "item must be a string."
                )
            )

        current_ids = {
            step.step_id
            for step
            in pipeline.steps
        }

        if set(
            order
        ) != current_ids:
            raise ValueError(
                (
                    "PIPELINE_ORDER must "
                    "contain every current "
                    "pipeline step exactly once."
                )
            )

        if len(
            order
        ) != len(
            current_ids
        ):
            raise ValueError(
                (
                    "PIPELINE_ORDER contains "
                    "duplicate pipeline steps."
                )
            )

        step_map = {
            step.step_id: step
            for step
            in pipeline.steps
        }

        pipeline.steps = [
            step_map[
                step_id
            ]
            for step_id
            in order
        ]

    # =========================================================
    # Band-pass
    # =========================================================

    if (
        "BANDPASS_ENABLED"
        in values
    ):
        bandpass.enabled = (
            _require_bool(
                "BANDPASS_ENABLED",
                values[
                    "BANDPASS_ENABLED"
                ],
            )
        )

    if (
        "HIGHPASS_HZ"
        in values
    ):
        bandpass.parameters[
            "highpass_hz"
        ] = (
            _require_positive_number(
                "HIGHPASS_HZ",
                values[
                    "HIGHPASS_HZ"
                ],
            )
        )

    if (
        "LOWPASS_HZ"
        in values
    ):
        bandpass.parameters[
            "lowpass_hz"
        ] = (
            _require_positive_number(
                "LOWPASS_HZ",
                values[
                    "LOWPASS_HZ"
                ],
            )
        )

    if (
        "FILTER_ORDER"
        in values
    ):
        order_value = (
            values[
                "FILTER_ORDER"
            ]
        )

        if (
            isinstance(
                order_value,
                bool,
            )
            or not isinstance(
                order_value,
                int,
            )
            or order_value < 1
            or order_value > 10
        ):
            raise ValueError(
                (
                    "FILTER_ORDER must "
                    "be an integer "
                    "from 1 to 10."
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

    if (
        lowpass
        <= highpass
    ):
        raise ValueError(
            (
                "LOWPASS_HZ must "
                "be greater than "
                "HIGHPASS_HZ."
            )
        )

    # =========================================================
    # Notch
    # =========================================================

    if (
        "NOTCH_ENABLED"
        in values
    ):
        notch.enabled = (
            _require_bool(
                "NOTCH_ENABLED",
                values[
                    "NOTCH_ENABLED"
                ],
            )
        )

    if (
        "NOTCH_HZ"
        in values
    ):
        notch.parameters[
            "frequency_hz"
        ] = (
            _require_positive_number(
                "NOTCH_HZ",
                values[
                    "NOTCH_HZ"
                ],
            )
        )

    if (
        "NOTCH_Q"
        in values
    ):
        notch.parameters[
            "quality_factor"
        ] = (
            _require_positive_number(
                "NOTCH_Q",
                values[
                    "NOTCH_Q"
                ],
            )
        )

    # =========================================================
    # Reference
    # =========================================================

    if (
        "AVERAGE_REFERENCE_ENABLED"
        in values
    ):
        reference.enabled = (
            _require_bool(
                "AVERAGE_REFERENCE_ENABLED",
                values[
                    "AVERAGE_REFERENCE_ENABLED"
                ],
            )
        )

    if (
        "REFERENCE_EXCLUDE"
        in values
    ):
        excluded = (
            values[
                "REFERENCE_EXCLUDE"
            ]
        )

        if not isinstance(
            excluded,
            list,
        ):
            raise ValueError(
                (
                    "REFERENCE_EXCLUDE "
                    "must be a list."
                )
            )

        if not all(
            isinstance(
                channel,
                str,
            )
            for channel
            in excluded
        ):
            raise ValueError(
                (
                    "Every REFERENCE_EXCLUDE "
                    "item must be a string."
                )
            )

        reference.parameters[
            "exclude_channels"
        ] = list(
            excluded
        )

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
            (
                f"{name} must be "
                "True or False."
            )
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
            (
                f"{name} must "
                "be a number."
            )
        )

    number = float(
        value
    )

    if number <= 0:
        raise ValueError(
            (
                f"{name} must "
                "be greater than 0."
            )
        )

    return number