import ast
import copy

from synaptix.models.bridge import (
    BridgeDetectionSettings,
)
from synaptix.models.pipeline import (
    PipelineConfiguration,
)


SUPPORTED_SETTINGS = {
    "PIPELINE_ORDER",
    "BAD_CHANNELS",

    "BRIDGE_DETECTION_ENABLED",
    "BRIDGE_LM_CUTOFF_UV2",
    "BRIDGE_EPOCH_THRESHOLD",
    "BRIDGE_L_FREQ",
    "BRIDGE_H_FREQ",
    "BRIDGE_EPOCH_DURATION",
    "CONFIRMED_BRIDGES",

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
            value = ast.literal_eval(
                node.value
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


# =============================================================
# Bad channels
# =============================================================


def parse_bad_channels(
    script: str,
) -> list[str] | None:
    values = _extract_values(
        script
    )

    if (
        "BAD_CHANNELS"
        not in values
    ):
        return None

    channels = values[
        "BAD_CHANNELS"
    ]

    return _require_string_list(
        "BAD_CHANNELS",
        channels,
    )


# =============================================================
# Bridge configuration
# =============================================================


def parse_bridge_settings(
    script: str,
    current_settings: BridgeDetectionSettings,
) -> BridgeDetectionSettings:
    values = _extract_values(
        script
    )

    settings = (
        current_settings.model_copy(
            deep=True
        )
    )

    if (
        "BRIDGE_DETECTION_ENABLED"
        in values
    ):
        settings.enabled = _require_bool(
            "BRIDGE_DETECTION_ENABLED",
            values[
                "BRIDGE_DETECTION_ENABLED"
            ],
        )

    if (
        "BRIDGE_LM_CUTOFF_UV2"
        in values
    ):
        settings.lm_cutoff_uv2 = (
            _require_positive_number(
                "BRIDGE_LM_CUTOFF_UV2",
                values[
                    "BRIDGE_LM_CUTOFF_UV2"
                ],
            )
        )

    if (
        "BRIDGE_EPOCH_THRESHOLD"
        in values
    ):
        threshold = (
            _require_positive_number(
                "BRIDGE_EPOCH_THRESHOLD",
                values[
                    "BRIDGE_EPOCH_THRESHOLD"
                ],
            )
        )

        if threshold > 1:
            raise ValueError(
                (
                    "BRIDGE_EPOCH_THRESHOLD "
                    "must be between 0 and 1."
                )
            )

        settings.epoch_threshold = (
            threshold
        )

    if (
        "BRIDGE_L_FREQ"
        in values
    ):
        settings.low_frequency_hz = (
            _require_positive_number(
                "BRIDGE_L_FREQ",
                values[
                    "BRIDGE_L_FREQ"
                ],
            )
        )

    if (
        "BRIDGE_H_FREQ"
        in values
    ):
        settings.high_frequency_hz = (
            _require_positive_number(
                "BRIDGE_H_FREQ",
                values[
                    "BRIDGE_H_FREQ"
                ],
            )
        )

    if (
        settings.high_frequency_hz
        <= settings.low_frequency_hz
    ):
        raise ValueError(
            (
                "BRIDGE_H_FREQ must be greater "
                "than BRIDGE_L_FREQ."
            )
        )

    if (
        "BRIDGE_EPOCH_DURATION"
        in values
    ):
        settings.epoch_duration_seconds = (
            _require_positive_number(
                "BRIDGE_EPOCH_DURATION",
                values[
                    "BRIDGE_EPOCH_DURATION"
                ],
            )
        )

    return settings


def parse_confirmed_bridges(
    script: str,
) -> list[
    tuple[str, str]
] | None:
    values = _extract_values(
        script
    )

    if (
        "CONFIRMED_BRIDGES"
        not in values
    ):
        return None

    raw_pairs = values[
        "CONFIRMED_BRIDGES"
    ]

    if not isinstance(
        raw_pairs,
        list,
    ):
        raise ValueError(
            (
                "CONFIRMED_BRIDGES "
                "must be a list."
            )
        )

    pairs: list[
        tuple[str, str]
    ] = []

    for pair in raw_pairs:
        if (
            not isinstance(
                pair,
                (
                    list,
                    tuple,
                ),
            )
            or len(
                pair
            )
            != 2
            or not all(
                isinstance(
                    channel,
                    str,
                )
                for channel
                in pair
            )
        ):
            raise ValueError(
                (
                    "Each CONFIRMED_BRIDGES item "
                    "must contain exactly two "
                    "channel-name strings."
                )
            )

        normalized = (
            pair[
                0
            ],
            pair[
                1
            ],
        )

        if normalized not in pairs:
            pairs.append(
                normalized
            )

    return pairs


# =============================================================
# Pipeline
# =============================================================


def parse_pipeline_script(
    script: str,
    current_pipeline: PipelineConfiguration,
) -> PipelineConfiguration:
    values = _extract_values(
        script
    )

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
        order = values[
            "PIPELINE_ORDER"
        ]

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

        current_ids = {
            step.step_id
            for step
            in pipeline.steps
        }

        if (
            len(
                order
            )
            != len(
                current_ids
            )
            or set(
                order
            )
            != current_ids
        ):
            raise ValueError(
                (
                    "PIPELINE_ORDER must "
                    "contain every current "
                    "pipeline step exactly once."
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
        bandpass.enabled = _require_bool(
            "BANDPASS_ENABLED",
            values[
                "BANDPASS_ENABLED"
            ],
        )

    if (
        "HIGHPASS_HZ"
        in values
    ):
        bandpass.parameters[
            "highpass_hz"
        ] = _require_positive_number(
            "HIGHPASS_HZ",
            values[
                "HIGHPASS_HZ"
            ],
        )

    if (
        "LOWPASS_HZ"
        in values
    ):
        bandpass.parameters[
            "lowpass_hz"
        ] = _require_positive_number(
            "LOWPASS_HZ",
            values[
                "LOWPASS_HZ"
            ],
        )

    if (
        "FILTER_ORDER"
        in values
    ):
        order_value = values[
            "FILTER_ORDER"
        ]

        if (
            isinstance(
                order_value,
                bool,
            )
            or not isinstance(
                order_value,
                int,
            )
            or not (
                1
                <= order_value
                <= 10
            )
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

    if lowpass <= highpass:
        raise ValueError(
            (
                "LOWPASS_HZ must be "
                "greater than HIGHPASS_HZ."
            )
        )

    # =========================================================
    # Notch
    # =========================================================

    if (
        "NOTCH_ENABLED"
        in values
    ):
        notch.enabled = _require_bool(
            "NOTCH_ENABLED",
            values[
                "NOTCH_ENABLED"
            ],
        )

    if (
        "NOTCH_HZ"
        in values
    ):
        notch.parameters[
            "frequency_hz"
        ] = _require_positive_number(
            "NOTCH_HZ",
            values[
                "NOTCH_HZ"
            ],
        )

    if (
        "NOTCH_Q"
        in values
    ):
        notch.parameters[
            "quality_factor"
        ] = _require_positive_number(
            "NOTCH_Q",
            values[
                "NOTCH_Q"
            ],
        )

    # =========================================================
    # Reference
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

    if (
        "REFERENCE_EXCLUDE"
        in values
    ):
        reference.parameters[
            "exclude_channels"
        ] = _require_string_list(
            "REFERENCE_EXCLUDE",
            values[
                "REFERENCE_EXCLUDE"
            ],
        )

    return pipeline


# =============================================================
# Validation helpers
# =============================================================


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
                f"{name} must be "
                "greater than 0."
            )
        )

    return number


def _require_string_list(
    name: str,
    value: object,
) -> list[str]:
    if not isinstance(
        value,
        list,
    ):
        raise ValueError(
            (
                f"{name} must "
                "be a list."
            )
        )

    if not all(
        isinstance(
            item,
            str,
        )
        for item
        in value
    ):
        raise ValueError(
            (
                f"Every {name} item "
                "must be a string."
            )
        )

    if len(
        value
    ) != len(
        set(
            value
        )
    ):
        raise ValueError(
            (
                f"{name} cannot "
                "contain duplicates."
            )
        )

    return list(
        value
    )