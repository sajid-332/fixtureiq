"""
FixtureIQ Stage 9.8.3
INTELLIGENCE INTEGRITY VERIFICATION

Purpose
-------
Independently verify the intelligence derived after the locked Stage 7
prediction entered Stage 9.

Verifies:
- Stage 9.8.1 foundation remains current
- Stage 9.8.2 prediction-integrity evidence remains current
- Stage 9.2 base/context values remain unchanged
- top / second probability and probability margin
- six contextual gap metrics
- five-signal context support score
- prediction/context alignment
- Shannon entropy and normalized entropy
- confidence band
- uncertainty band
- deterministic explanation headline
- deterministic explanation summary semantics
- no protected artifact mutation

This gate DOES NOT:
- run the prediction model
- rebuild intelligence
- tune probabilities
- alter predictions
- alter context
- use bookmaker odds
- use future results
- promote Stage 9

Only Stage 9.8.5 may promote Stage 9.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


# ============================================================
# Project paths
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BASE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BASE_DIR),
    )


INTELLIGENCE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "intelligence"
)


CONTRACT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract.json"
)

BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)

BASE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)

INTELLIGENCE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

INTELLIGENCE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)

FOUNDATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_1_foundation_verification.json"
)

PREDICTION_INTEGRITY_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_2_prediction_integrity_verification.json"
)

OUTPUT_FILE = (
    INTELLIGENCE_DIR
    / "stage9_8_3_intelligence_integrity_verification.json"
)


# ============================================================
# Locked Stage 9 intelligence fields
# ============================================================

PROBABILITY_FIELDS = [
    "stage7_prob_home_win",
    "stage7_prob_draw",
    "stage7_prob_away_win",
]


DERIVED_FIELDS = [
    "stage9_top_probability",
    "stage9_second_probability",
    "stage9_probability_margin",

    "stage9_entropy",
    "stage9_normalized_entropy",

    "stage9_confidence_band",
    "stage9_uncertainty_band",

    "stage9_league_position_gap",
    "stage9_points_gap",
    "stage9_goal_difference_gap",

    "stage9_recent_points_gap",
    "stage9_recent_goal_difference_gap",
    "stage9_venue_form_points_gap",

    "stage9_context_support_score",
    "stage9_context_alignment",

    "stage9_explanation_headline",
    "stage9_explanation_summary",
]


CONTEXT_SOURCE_FIELDS = [
    "home_team_position",
    "away_team_position",

    "home_team_points",
    "away_team_points",

    "home_team_goal_difference",
    "away_team_goal_difference",

    "home_team_recent_points",
    "away_team_recent_points",

    "home_team_recent_goal_difference",
    "away_team_recent_goal_difference",

    "home_team_home_recent_points",
    "away_team_away_recent_points",
]


ALLOWED_BANDS = {
    "VERY_LOW",
    "LOW",
    "MODERATE",
    "HIGH",
    "VERY_HIGH",
}


ALLOWED_ALIGNMENTS = {
    "SUPPORTIVE",
    "MIXED",
    "CONTRADICTORY",
    "NEUTRAL",
}


MISSING_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "na",
    "n/a",
}


# ============================================================
# Helpers
# ============================================================

def load_json(path: Path) -> dict:

    if not path.exists():
        raise RuntimeError(
            f"Missing JSON artifact: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Expected JSON object: {path}"
        )

    return payload


def load_csv(
    path: Path,
) -> tuple[list[str], list[dict[str, str]]]:

    if not path.exists():
        raise RuntimeError(
            f"Missing CSV artifact: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        fields = list(
            reader.fieldnames
            or []
        )

        rows = [
            dict(row)
            for row in reader
        ]

    if not fields:
        raise RuntimeError(
            f"No CSV columns: {path}"
        )

    if not rows:
        raise RuntimeError(
            f"No CSV rows: {path}"
        )

    return fields, rows


def sha256_file(path: Path) -> str:

    if not path.exists():
        raise RuntimeError(
            f"Missing artifact: {path}"
        )

    digest = hashlib.sha256()

    with path.open("rb") as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def relative_path(path: Path) -> str:

    return (
        str(
            path.resolve().relative_to(
                BASE_DIR.resolve()
            )
        )
        .replace("\\", "/")
    )


def save_json_atomic(
    path: Path,
    payload: dict,
) -> None:

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )

    temporary.replace(path)


def check(
    label: str,
    condition,
    failures: list[str],
) -> bool:

    passed = bool(condition)

    print(
        f"{label}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:
        failures.append(label)

    return passed


def optional_decimal(
    row: dict[str, str],
    field: str,
) -> Decimal | None:

    raw = str(
        row.get(
            field,
            "",
        )
    ).strip()

    if raw.casefold() in MISSING_VALUES:
        return None

    try:
        value = Decimal(raw)

    except InvalidOperation as exc:
        raise RuntimeError(
            f"Invalid number: {field}={raw!r}"
        ) from exc

    if not value.is_finite():
        return None

    return value


def required_decimal(
    row: dict[str, str],
    field: str,
    fixture_id: str,
) -> Decimal:

    value = optional_decimal(
        row,
        field,
    )

    if value is None:
        raise RuntimeError(
            (
                f"Required numeric field missing: "
                f"{fixture_id} / {field}"
            )
        )

    return value


def numeric_equal(
    left: Decimal,
    right: Decimal,
    tolerance: Decimal = Decimal("0"),
) -> bool:

    return (
        abs(left - right)
        <=
        tolerance
    )


def float_equal(
    left: float,
    right: float,
    tolerance: float = 5e-12,
) -> bool:

    return math.isclose(
        left,
        right,
        rel_tol=0.0,
        abs_tol=tolerance,
    )


def build_index(
    rows: list[dict[str, str]],
    name: str,
) -> tuple[
    dict[str, dict[str, str]],
    list[str],
]:

    result = {}
    order = []

    for row in rows:

        fixture_id = str(
            row.get(
                "fixture_id",
                "",
            )
        ).strip()

        if not fixture_id:
            raise RuntimeError(
                f"{name}: empty fixture_id"
            )

        if fixture_id in result:
            raise RuntimeError(
                (
                    f"{name}: duplicate "
                    f"fixture_id={fixture_id}"
                )
            )

        result[fixture_id] = row
        order.append(fixture_id)

    return result, order


def calculate_gap(
    first: Decimal | None,
    second: Decimal | None,
) -> Decimal | None:

    if (
        first is None
        or
        second is None
    ):
        return None

    return first - second


def sign_signal(
    value: Decimal | None,
) -> int:

    if value is None:
        return 0

    if value > 0:
        return 1

    if value < 0:
        return -1

    return 0


def confidence_band(
    confidence: float,
) -> str:

    if confidence < 0.40:
        return "VERY_LOW"

    if confidence < 0.50:
        return "LOW"

    if confidence < 0.60:
        return "MODERATE"

    if confidence < 0.70:
        return "HIGH"

    return "VERY_HIGH"


def uncertainty_band(
    normalized_entropy: float,
) -> str:

    if normalized_entropy < 0.20:
        return "VERY_LOW"

    if normalized_entropy < 0.40:
        return "LOW"

    if normalized_entropy < 0.60:
        return "MODERATE"

    if normalized_entropy < 0.80:
        return "HIGH"

    return "VERY_HIGH"


def expected_alignment(
    predicted_label: str,
    support_score: int,
) -> str:

    if predicted_label == "Home Win":

        if support_score >= 2:
            return "SUPPORTIVE"

        if support_score <= -2:
            return "CONTRADICTORY"

        if support_score == 0:
            return "NEUTRAL"

        return "MIXED"

    if predicted_label == "Away Win":

        if support_score <= -2:
            return "SUPPORTIVE"

        if support_score >= 2:
            return "CONTRADICTORY"

        if support_score == 0:
            return "NEUTRAL"

        return "MIXED"

    if predicted_label == "Draw":

        absolute_score = abs(
            support_score
        )

        if absolute_score <= 1:
            return "SUPPORTIVE"

        if absolute_score == 2:
            return "MIXED"

        return "CONTRADICTORY"

    raise RuntimeError(
        (
            "Unknown Stage 7 predicted label: "
            f"{predicted_label!r}"
        )
    )


def expected_headline(
    predicted_label: str,
    alignment: str,
    home_team: str,
    away_team: str,
) -> str:

    if predicted_label == "Home Win":

        templates = {

            "SUPPORTIVE":
                (
                    f"Model leans {home_team}; "
                    "context supports the home side"
                ),

            "CONTRADICTORY":
                (
                    f"Model leans {home_team}; "
                    f"context favors {away_team}"
                ),

            "MIXED":
                (
                    f"Model leans {home_team}; "
                    "context is mixed"
                ),

            "NEUTRAL":
                (
                    f"Model leans {home_team}; "
                    "context is balanced"
                ),
        }

        return templates[alignment]

    if predicted_label == "Away Win":

        templates = {

            "SUPPORTIVE":
                (
                    f"Model leans {away_team}; "
                    "context supports the away side"
                ),

            "CONTRADICTORY":
                (
                    f"Model leans {away_team}; "
                    f"context favors {home_team}"
                ),

            "MIXED":
                (
                    f"Model leans {away_team}; "
                    "context is mixed"
                ),

            "NEUTRAL":
                (
                    f"Model leans {away_team}; "
                    "context is balanced"
                ),
        }

        return templates[alignment]

    if predicted_label == "Draw":

        templates = {

            "SUPPORTIVE":
                (
                    "Model leans draw; "
                    "context is relatively balanced"
                ),

            "MIXED":
                (
                    "Model leans draw; "
                    "context shows a mild side advantage"
                ),

            "CONTRADICTORY":
                (
                    "Model leans draw; "
                    "context shows a clearer side advantage"
                ),

            "NEUTRAL":
                (
                    "Model leans draw; "
                    "context is neutral"
                ),
        }

        return templates[alignment]

    raise RuntimeError(
        f"Unknown prediction label: {predicted_label}"
    )


def normalized_word(
    value: str,
) -> str:

    return (
        str(value)
        .strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


def displayed_number_matches(
    text_number: str,
    expected: float,
) -> bool:

    try:
        observed = float(
            text_number
        )

    except ValueError:
        return False

    if "." in text_number:

        decimal_places = len(
            text_number.split(
                ".",
                1,
            )[1]
        )

    else:
        decimal_places = 0

    rounding_unit = (
        10 ** (-decimal_places)
    )

    tolerance = (
        rounding_unit / 2
        +
        1e-10
    )

    return (
        abs(
            observed
            -
            expected
        )
        <=
        tolerance
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 72)

    print(
        "FixtureIQ Stage 9.8.3"
    )

    print(
        "INTELLIGENCE INTEGRITY VERIFICATION"
    )

    print("=" * 72)

    failures: list[str] = []

    # ========================================================
    # 1. Required artifacts
    # ========================================================

    print(
        "\n1. REQUIRED ARTIFACTS"
    )

    required_files = [
        CONTRACT_FILE,
        BASE_FILE,
        BASE_REPORT_FILE,
        INTELLIGENCE_FILE,
        INTELLIGENCE_REPORT_FILE,
        FOUNDATION_FILE,
        PREDICTION_INTEGRITY_FILE,
    ]

    for path in required_files:

        check(
            path.name,
            path.exists(),
            failures,
        )

    if failures:

        print(
            "\n" + "=" * 72
        )

        print(
            "STAGE 9.8.3: FAIL"
        )

        print(
            "INTELLIGENCE INTEGRITY: NOT VERIFIED"
        )

        print("=" * 72)

        sys.exit(1)

    protected_before = {

        relative_path(path):
            sha256_file(path)

        for path in required_files
    }

    # ========================================================
    # 2. Previous gates
    # ========================================================

    print(
        "\n2. PREVIOUS FINAL-GATE EVIDENCE"
    )

    foundation = load_json(
        FOUNDATION_FILE
    )

    prediction_integrity = load_json(
        PREDICTION_INTEGRITY_FILE
    )

    check(
        "Stage 9.8.1 PASS",
        foundation.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 9.8.2 PASS",
        prediction_integrity.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Prediction integrity VERIFIED",
        prediction_integrity.get(
            "prediction_integrity"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.8.2 authorized 9.8.3",
        prediction_integrity.get(
            "stage9_ready_for_9_8_3"
        )
        is True,
        failures,
    )

    # 9.8.2 itself pinned these Stage 9 inputs.

    previous_dependencies = (
        prediction_integrity.get(
            "dependency_identity",
            {}
        )
    )

    for path in [
        BASE_FILE,
        BASE_REPORT_FILE,
        INTELLIGENCE_FILE,
    ]:

        key = relative_path(path)

        check(
            (
                f"{path.name} unchanged "
                "since 9.8.2"
            ),
            previous_dependencies.get(
                key,
                {}
            ).get(
                "sha256"
            )
            ==
            sha256_file(path),
            failures,
        )

    # ========================================================
    # 3. Current intelligence report
    # ========================================================

    print(
        "\n3. VERIFIED INTELLIGENCE FOUNDATION"
    )

    report = load_json(
        INTELLIGENCE_REPORT_FILE
    )

    check(
        "Intelligence report PASS",
        report.get(
            "status"
        )
        ==
        "PASS",
        failures,
    )

    check(
        "Stage 9.3 COMPLETE",
        report.get(
            "stage_9_3_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.3 VERIFIED",
        report.get(
            "derived_match_intelligence"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.4 COMPLETE",
        report.get(
            "stage_9_4_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.4 VERIFIED",
        report.get(
            "confidence_uncertainty_layer"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Stage 9.5 COMPLETE",
        report.get(
            "stage_9_5_complete"
        )
        is True,
        failures,
    )

    check(
        "Stage 9.5 VERIFIED",
        report.get(
            "match_explanation_engine"
        )
        ==
        "VERIFIED",
        failures,
    )

    check(
        "Final intelligence SHA current",
        report.get(
            "output_artifact",
            {}
        ).get(
            "sha256"
        )
        ==
        sha256_file(
            INTELLIGENCE_FILE
        ),
        failures,
    )

    # ========================================================
    # 4. Load base and final intelligence
    # ========================================================

    print(
        "\n4. BASE / FINAL INTELLIGENCE DATASETS"
    )

    (
        base_fields,
        base_rows,
    ) = load_csv(
        BASE_FILE
    )

    (
        final_fields,
        final_rows,
    ) = load_csv(
        INTELLIGENCE_FILE
    )

    check(
        "Base/final row count exact",
        len(base_rows)
        ==
        len(final_rows),
        failures,
    )

    for field in CONTEXT_SOURCE_FIELDS:

        check(
            f"Context source exists: {field}",
            field in final_fields,
            failures,
        )

    for field in DERIVED_FIELDS:

        check(
            f"Derived field exists: {field}",
            field in final_fields,
            failures,
        )

    for field in [
        "fixture_id",
        "home_team_name",
        "away_team_name",
        "stage7_predicted_label",
        "stage7_confidence",
        *PROBABILITY_FIELDS,
    ]:

        check(
            f"Required intelligence field exists: {field}",
            field in final_fields,
            failures,
        )

    # ========================================================
    # 5. Fixture/base preservation
    # ========================================================

    print(
        "\n5. BASE CONTEXT PRESERVATION"
    )

    try:

        base_index, base_order = (
            build_index(
                base_rows,
                "match_intelligence_base",
            )
        )

        final_index, final_order = (
            build_index(
                final_rows,
                "match_intelligence",
            )
        )

        indices_valid = True

    except Exception as exc:

        print(
            "Index error:",
            exc,
        )

        base_index = {}
        final_index = {}

        base_order = []
        final_order = []

        indices_valid = False

    check(
        "Fixture IDs unique",
        indices_valid,
        failures,
    )

    check(
        "Base/final fixture set exact",
        set(base_index)
        ==
        set(final_index),
        failures,
    )

    check(
        "Base/final fixture order exact",
        base_order
        ==
        final_order,
        failures,
    )

    base_values_preserved = True

    base_value_checks = 0

    first_base_error = None

    if (
        indices_valid
        and
        set(base_index)
        ==
        set(final_index)
    ):

        for fixture_id in base_order:

            base_row = base_index[
                fixture_id
            ]

            final_row = final_index[
                fixture_id
            ]

            for field in base_fields:

                base_value_checks += 1

                if (
                    base_row.get(
                        field,
                        ""
                    )
                    !=
                    final_row.get(
                        field,
                        ""
                    )
                ):

                    base_values_preserved = False

                    if first_base_error is None:

                        first_base_error = (
                            fixture_id,
                            field,
                            base_row.get(
                                field
                            ),
                            final_row.get(
                                field
                            ),
                        )

    check(
        "All Stage 9.2 base values preserved exactly",
        base_values_preserved,
        failures,
    )

    if first_base_error:

        print(
            "First base mutation:",
            first_base_error,
        )

    # ========================================================
    # 6. Independent intelligence recomputation
    # ========================================================

    print(
        "\n6. DERIVED MATCH INTELLIGENCE"
    )

    probability_metrics_valid = True
    gaps_valid = True
    support_scores_valid = True
    alignments_valid = True

    entropy_valid = True
    normalized_entropy_valid = True
    confidence_bands_valid = True
    uncertainty_bands_valid = True

    headlines_valid = True
    summaries_valid = True

    semantic_fixture_checks = 0

    first_probability_metric_error = None
    first_gap_error = None
    first_support_error = None
    first_alignment_error = None
    first_entropy_error = None
    first_band_error = None
    first_headline_error = None
    first_summary_error = None

    if indices_valid:

        for fixture_id in final_order:

            row = final_index[
                fixture_id
            ]

            # ------------------------------------------------
            # Stage 7 probability vector
            # ------------------------------------------------

            probabilities_decimal = [

                required_decimal(
                    row,
                    "stage7_prob_home_win",
                    fixture_id,
                ),

                required_decimal(
                    row,
                    "stage7_prob_draw",
                    fixture_id,
                ),

                required_decimal(
                    row,
                    "stage7_prob_away_win",
                    fixture_id,
                ),
            ]

            sorted_probabilities = sorted(
                probabilities_decimal,
                reverse=True,
            )

            expected_top = (
                sorted_probabilities[0]
            )

            expected_second = (
                sorted_probabilities[1]
            )

            expected_margin = (
                expected_top
                -
                expected_second
            )

            actual_top = required_decimal(
                row,
                "stage9_top_probability",
                fixture_id,
            )

            actual_second = required_decimal(
                row,
                "stage9_second_probability",
                fixture_id,
            )

            actual_margin = required_decimal(
                row,
                "stage9_probability_margin",
                fixture_id,
            )

            probability_metric_ok = (
                numeric_equal(
                    actual_top,
                    expected_top,
                    Decimal("0.000000000001"),
                )
                and
                numeric_equal(
                    actual_second,
                    expected_second,
                    Decimal("0.000000000001"),
                )
                and
                numeric_equal(
                    actual_margin,
                    expected_margin,
                    Decimal("0.000000000001"),
                )
            )

            if not probability_metric_ok:

                probability_metrics_valid = False

                if first_probability_metric_error is None:

                    first_probability_metric_error = (
                        fixture_id,
                        expected_top,
                        actual_top,
                        expected_second,
                        actual_second,
                        expected_margin,
                        actual_margin,
                    )

            # ------------------------------------------------
            # Six locked contextual gaps
            # ------------------------------------------------

            home_position = optional_decimal(
                row,
                "home_team_position",
            )

            away_position = optional_decimal(
                row,
                "away_team_position",
            )

            home_points = optional_decimal(
                row,
                "home_team_points",
            )

            away_points = optional_decimal(
                row,
                "away_team_points",
            )

            home_gd = optional_decimal(
                row,
                "home_team_goal_difference",
            )

            away_gd = optional_decimal(
                row,
                "away_team_goal_difference",
            )

            home_recent_points = optional_decimal(
                row,
                "home_team_recent_points",
            )

            away_recent_points = optional_decimal(
                row,
                "away_team_recent_points",
            )

            home_recent_gd = optional_decimal(
                row,
                "home_team_recent_goal_difference",
            )

            away_recent_gd = optional_decimal(
                row,
                "away_team_recent_goal_difference",
            )

            home_venue_points = optional_decimal(
                row,
                "home_team_home_recent_points",
            )

            away_venue_points = optional_decimal(
                row,
                "away_team_away_recent_points",
            )

            expected_gaps = {

                # Positive = home advantage.
                "stage9_league_position_gap":
                    calculate_gap(
                        away_position,
                        home_position,
                    ),

                "stage9_points_gap":
                    calculate_gap(
                        home_points,
                        away_points,
                    ),

                "stage9_goal_difference_gap":
                    calculate_gap(
                        home_gd,
                        away_gd,
                    ),

                "stage9_recent_points_gap":
                    calculate_gap(
                        home_recent_points,
                        away_recent_points,
                    ),

                "stage9_recent_goal_difference_gap":
                    calculate_gap(
                        home_recent_gd,
                        away_recent_gd,
                    ),

                "stage9_venue_form_points_gap":
                    calculate_gap(
                        home_venue_points,
                        away_venue_points,
                    ),
            }

            fixture_gaps_ok = True

            for (
                field,
                expected_value,
            ) in expected_gaps.items():

                actual_value = optional_decimal(
                    row,
                    field,
                )

                if expected_value is None:

                    # Unavailable source context is allowed to
                    # remain unavailable in the derived gap.
                    gap_ok = (
                        actual_value
                        is None
                    )

                else:

                    gap_ok = (
                        actual_value
                        is not None
                        and
                        numeric_equal(
                            actual_value,
                            expected_value,
                            Decimal(
                                "0.000000000001"
                            ),
                        )
                    )

                if not gap_ok:

                    fixture_gaps_ok = False

                    if first_gap_error is None:

                        first_gap_error = (
                            fixture_id,
                            field,
                            expected_value,
                            actual_value,
                        )

            if not fixture_gaps_ok:
                gaps_valid = False

            # ------------------------------------------------
            # Fixed five-signal support score
            # ------------------------------------------------

            support_signals = [

                sign_signal(
                    expected_gaps[
                        "stage9_league_position_gap"
                    ]
                ),

                sign_signal(
                    expected_gaps[
                        "stage9_points_gap"
                    ]
                ),

                sign_signal(
                    expected_gaps[
                        "stage9_goal_difference_gap"
                    ]
                ),

                sign_signal(
                    expected_gaps[
                        "stage9_recent_points_gap"
                    ]
                ),

                sign_signal(
                    expected_gaps[
                        "stage9_venue_form_points_gap"
                    ]
                ),
            ]

            expected_support_score = sum(
                support_signals
            )

            actual_support_decimal = (
                required_decimal(
                    row,
                    "stage9_context_support_score",
                    fixture_id,
                )
            )

            support_integer_like = (
                actual_support_decimal
                ==
                actual_support_decimal.to_integral_value()
            )

            actual_support_score = int(
                actual_support_decimal
            )

            support_ok = (
                support_integer_like
                and
                -5
                <=
                actual_support_score
                <=
                5
                and
                actual_support_score
                ==
                expected_support_score
            )

            if not support_ok:

                support_scores_valid = False

                if first_support_error is None:

                    first_support_error = (
                        fixture_id,
                        support_signals,
                        expected_support_score,
                        actual_support_score,
                    )

            # ------------------------------------------------
            # Alignment
            # ------------------------------------------------

            predicted_label = str(
                row.get(
                    "stage7_predicted_label",
                    "",
                )
            ).strip()

            expected_context_alignment = (
                expected_alignment(
                    predicted_label,
                    expected_support_score,
                )
            )

            actual_alignment = str(
                row.get(
                    "stage9_context_alignment",
                    "",
                )
            ).strip()

            if (
                actual_alignment
                !=
                expected_context_alignment
            ):

                alignments_valid = False

                if first_alignment_error is None:

                    first_alignment_error = (
                        fixture_id,
                        predicted_label,
                        expected_support_score,
                        expected_context_alignment,
                        actual_alignment,
                    )

            # ------------------------------------------------
            # Shannon entropy
            # ------------------------------------------------

            probabilities_float = [
                float(value)
                for value
                in probabilities_decimal
            ]

            expected_entropy = 0.0

            for probability in probabilities_float:

                if probability > 0:

                    expected_entropy -= (
                        probability
                        *
                        math.log(
                            probability
                        )
                    )

            expected_normalized_entropy = (
                expected_entropy
                /
                math.log(3.0)
            )

            actual_entropy = float(
                required_decimal(
                    row,
                    "stage9_entropy",
                    fixture_id,
                )
            )

            actual_normalized_entropy = float(
                required_decimal(
                    row,
                    "stage9_normalized_entropy",
                    fixture_id,
                )
            )

            if not float_equal(
                actual_entropy,
                expected_entropy,
                5e-12,
            ):

                entropy_valid = False

                if first_entropy_error is None:

                    first_entropy_error = (
                        fixture_id,
                        expected_entropy,
                        actual_entropy,
                    )

            if not float_equal(
                actual_normalized_entropy,
                expected_normalized_entropy,
                5e-12,
            ):

                normalized_entropy_valid = False

                if first_entropy_error is None:

                    first_entropy_error = (
                        fixture_id,
                        expected_normalized_entropy,
                        actual_normalized_entropy,
                    )

            # ------------------------------------------------
            # Confidence / uncertainty bands
            # ------------------------------------------------

            confidence = float(
                required_decimal(
                    row,
                    "stage7_confidence",
                    fixture_id,
                )
            )

            expected_confidence_band = (
                confidence_band(
                    confidence
                )
            )

            expected_uncertainty_band = (
                uncertainty_band(
                    expected_normalized_entropy
                )
            )

            actual_confidence_band = str(
                row.get(
                    "stage9_confidence_band",
                    "",
                )
            ).strip()

            actual_uncertainty_band = str(
                row.get(
                    "stage9_uncertainty_band",
                    "",
                )
            ).strip()

            if (
                actual_confidence_band
                not in
                ALLOWED_BANDS
                or
                actual_confidence_band
                !=
                expected_confidence_band
            ):

                confidence_bands_valid = False

                if first_band_error is None:

                    first_band_error = (
                        fixture_id,
                        "confidence",
                        expected_confidence_band,
                        actual_confidence_band,
                    )

            if (
                actual_uncertainty_band
                not in
                ALLOWED_BANDS
                or
                actual_uncertainty_band
                !=
                expected_uncertainty_band
            ):

                uncertainty_bands_valid = False

                if first_band_error is None:

                    first_band_error = (
                        fixture_id,
                        "uncertainty",
                        expected_uncertainty_band,
                        actual_uncertainty_band,
                    )

            # ------------------------------------------------
            # Deterministic explanation headline
            # ------------------------------------------------

            home_team = str(
                row.get(
                    "home_team_name",
                    "",
                )
            ).strip()

            away_team = str(
                row.get(
                    "away_team_name",
                    "",
                )
            ).strip()

            expected_title = expected_headline(
                predicted_label,
                expected_context_alignment,
                home_team,
                away_team,
            )

            actual_title = str(
                row.get(
                    "stage9_explanation_headline",
                    "",
                )
            ).strip()

            if actual_title != expected_title:

                headlines_valid = False

                if first_headline_error is None:

                    first_headline_error = (
                        fixture_id,
                        expected_title,
                        actual_title,
                    )

            # ------------------------------------------------
            # Deterministic explanation summary semantics
            # ------------------------------------------------

            summary = str(
                row.get(
                    "stage9_explanation_summary",
                    "",
                )
            ).strip()

            summary_ok = bool(summary)

            # Subject
            subject_match = re.search(
                (
                    r"Stage 7 gives\s+(.+?)\s+"
                    r"the highest probability at"
                ),
                summary,
                flags=re.IGNORECASE,
            )

            if predicted_label == "Home Win":
                expected_subjects = {
                    home_team.casefold()
                }

            elif predicted_label == "Away Win":
                expected_subjects = {
                    away_team.casefold()
                }

            else:
                # Stage 9.5's deterministic Draw explanation
                # uses "a draw" as the natural-language subject.
                # Accept the locked semantic equivalents while
                # still rejecting unrelated wording.
                expected_subjects = {
                    "draw",
                    "a draw",
                    "the draw",
                }

            if not subject_match:

                summary_ok = False

            else:

                observed_subject = (
                    subject_match
                    .group(1)
                    .strip()
                    .casefold()
                )

                if (
                    observed_subject
                    not in expected_subjects
                ):

                    summary_ok = False

            # Top probability percentage
            top_match = re.search(
                (
                    r"highest probability at\s+"
                    r"([0-9]+(?:\.[0-9]+)?)%"
                ),
                summary,
                flags=re.IGNORECASE,
            )

            if (
                not top_match
                or
                not displayed_number_matches(
                    top_match.group(1),
                    float(expected_top) * 100.0,
                )
            ):

                summary_ok = False

            # Margin percentage points
            margin_match = re.search(
                (
                    r"([0-9]+(?:\.[0-9]+)?)"
                    r"\s+percentage points above "
                    r"the next outcome"
                ),
                summary,
                flags=re.IGNORECASE,
            )

            if (
                not margin_match
                or
                not displayed_number_matches(
                    margin_match.group(1),
                    float(expected_margin) * 100.0,
                )
            ):

                summary_ok = False

            # Context score
            score_match = re.search(
                (
                    r"fixed context score is\s+"
                    r"([+-]?\d+)"
                ),
                summary,
                flags=re.IGNORECASE,
            )

            if (
                not score_match
                or
                int(
                    score_match.group(1)
                )
                !=
                expected_support_score
            ):

                summary_ok = False

            home_signal_count = sum(
                signal == 1
                for signal
                in support_signals
            )

            away_signal_count = sum(
                signal == -1
                for signal
                in support_signals
            )

            neutral_signal_count = sum(
                signal == 0
                for signal
                in support_signals
            )

            # Stage 9.5 explanation summaries use the
            # canonical team names rather than the literal
            # words "home" and "away".
            #
            # Example:
            #   2 signals favor Brentford,
            #   3 favor Chelsea,
            #   and 0 are neutral or unavailable.

            signals_match = re.search(
                (
                    r"(\d+)\s+signals favor\s+(.+?),\s+"
                    r"(\d+)\s+favor\s+(.+?),\s+and\s+"
                    r"(\d+)\s+are neutral or unavailable"
                ),
                summary,
                flags=re.IGNORECASE,
            )

            if not signals_match:

                summary_ok = False

            else:

                observed_home_count = int(
                    signals_match.group(1)
                )

                observed_home_team = (
                    signals_match
                    .group(2)
                    .strip()
                )

                observed_away_count = int(
                    signals_match.group(3)
                )

                observed_away_team = (
                    signals_match
                    .group(4)
                    .strip()
                )

                observed_neutral_count = int(
                    signals_match.group(5)
                )

                if (
                    observed_home_count
                    !=
                    home_signal_count
                ):

                    summary_ok = False

                if (
                    observed_away_count
                    !=
                    away_signal_count
                ):

                    summary_ok = False

                if (
                    observed_neutral_count
                    !=
                    neutral_signal_count
                ):

                    summary_ok = False

                if (
                    observed_home_team.casefold()
                    !=
                    home_team.casefold()
                ):

                    summary_ok = False

                if (
                    observed_away_team.casefold()
                    !=
                    away_team.casefold()
                ):

                    summary_ok = False

            # Alignment / confidence / uncertainty
            state_match = re.search(
                (
                    r"Context alignment is\s+([^;]+);\s+"
                    r"confidence is\s+([^ ]+)\s+and\s+"
                    r"uncertainty is\s+([^\.]+)"
                ),
                summary,
                flags=re.IGNORECASE,
            )

            if not state_match:

                summary_ok = False

            else:

                observed_alignment = normalized_word(
                    state_match.group(1)
                )

                observed_confidence = normalized_word(
                    state_match.group(2)
                )

                observed_uncertainty = normalized_word(
                    state_match.group(3)
                )

                if (
                    observed_alignment
                    !=
                    expected_context_alignment
                ):

                    summary_ok = False

                if (
                    observed_confidence
                    !=
                    expected_confidence_band
                ):

                    summary_ok = False

                if (
                    observed_uncertainty
                    !=
                    expected_uncertainty_band
                ):

                    summary_ok = False

            disclaimer = (
                "This interprets the existing prediction "
                "and does not alter or replace it."
            )

            if (
                disclaimer.casefold()
                not in
                summary.casefold()
            ):

                summary_ok = False

            # Avoid deterministic language becoming
            # a certainty / guarantee claim.
            forbidden_certainty_fragments = [
                "guaranteed win",
                "guaranteed winner",
                "certain win",
                "certain winner",
                "definitely will win",
                "100% certain",
                "100% guaranteed",
            ]

            lowered_summary = (
                summary.casefold()
            )

            if any(
                fragment
                in lowered_summary

                for fragment
                in forbidden_certainty_fragments
            ):

                summary_ok = False

            if not summary_ok:

                summaries_valid = False

                if first_summary_error is None:

                    first_summary_error = (
                        fixture_id,
                        summary,
                    )

            semantic_fixture_checks += 1

    # ========================================================
    # 7. Aggregate results
    # ========================================================

    check(
        "Top / second / margin recomputed exactly",
        probability_metrics_valid,
        failures,
    )

    check(
        "All six context gaps recomputed correctly",
        gaps_valid,
        failures,
    )

    check(
        "Five-signal support scores recomputed correctly",
        support_scores_valid,
        failures,
    )

    check(
        "Context alignments recomputed correctly",
        alignments_valid,
        failures,
    )

    check(
        "Shannon entropy recomputed correctly",
        entropy_valid,
        failures,
    )

    check(
        "Normalized entropy recomputed correctly",
        normalized_entropy_valid,
        failures,
    )

    check(
        "Confidence bands recomputed correctly",
        confidence_bands_valid,
        failures,
    )

    check(
        "Uncertainty bands recomputed correctly",
        uncertainty_bands_valid,
        failures,
    )

    check(
        "Explanation headlines deterministic",
        headlines_valid,
        failures,
    )

    check(
        "Explanation summaries semantically deterministic",
        summaries_valid,
        failures,
    )

    check(
        "Every fixture independently checked",
        semantic_fixture_checks
        ==
        len(final_rows),
        failures,
    )

    if first_probability_metric_error:
        print(
            "First probability metric error:",
            first_probability_metric_error,
        )

    if first_gap_error:
        print(
            "First gap error:",
            first_gap_error,
        )

    if first_support_error:
        print(
            "First support-score error:",
            first_support_error,
        )

    if first_alignment_error:
        print(
            "First alignment error:",
            first_alignment_error,
        )

    if first_entropy_error:
        print(
            "First entropy error:",
            first_entropy_error,
        )

    if first_band_error:
        print(
            "First band error:",
            first_band_error,
        )

    if first_headline_error:
        print(
            "First headline error:",
            first_headline_error,
        )

    if first_summary_error:
        print(
            "First summary error:",
            first_summary_error,
        )

    # ========================================================
    # 8. Contract safety boundary
    # ========================================================

    print(
        "\n8. INTELLIGENCE SAFETY BOUNDARY"
    )

    contract = load_json(
        CONTRACT_FILE
    )

    forbidden_operations = (
        contract.get(
            "stage_9_1_2",
            {}
        ).get(
            "forbidden_operations",
            []
        )
    )

    forbidden_text = (
        " ".join(
            str(value)
            for value
            in forbidden_operations
        )
        .casefold()
    )

    check(
        "Model mutation forbidden",
        (
            "model"
            in forbidden_text
            and
            (
                "retrain"
                in forbidden_text
                or
                "tuning"
                in forbidden_text
                or
                "reselection"
                in forbidden_text
            )
        ),
        failures,
    )

    check(
        "Probability mutation forbidden",
        "probability"
        in forbidden_text,
        failures,
    )

    check(
        "Context-as-model-feature forbidden",
        (
            "context"
            in forbidden_text
            and
            "feature"
            in forbidden_text
        ),
        failures,
    )

    check(
        "No model execution performed by 9.8.3",
        True,
        failures,
    )

    check(
        "No provider fetch performed by 9.8.3",
        True,
        failures,
    )

    check(
        "No intelligence rebuild performed by 9.8.3",
        True,
        failures,
    )

    # ========================================================
    # 9. Write protection
    # ========================================================

    print(
        "\n9. INTELLIGENCE WRITE PROTECTION"
    )

    for path in required_files:

        key = relative_path(path)

        check(
            f"{path.name} unchanged",
            sha256_file(path)
            ==
            protected_before[key],
            failures,
        )

    # ========================================================
    # 10. Save evidence
    # ========================================================

    print(
        "\n10. SAVE STAGE 9.8.3 EVIDENCE"
    )

    overall_pass = (
        len(failures)
        ==
        0
    )

    if overall_pass:

        verified_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        evidence = {

            "stage":
                "9.8.3",

            "name":
                "INTELLIGENCE_INTEGRITY_VERIFICATION",

            "status":
                "PASS",

            "stage_9_8_3_complete":
                True,

            "intelligence_integrity":
                "VERIFIED",

            "verified_at_utc":
                verified_at,

            "fixture_count":
                len(final_rows),

            "integrity": {

                "stage9_base_values_preserved_exactly":
                    True,

                "top_probability_verified":
                    True,

                "second_probability_verified":
                    True,

                "probability_margin_verified":
                    True,

                "league_position_gap_verified":
                    True,

                "points_gap_verified":
                    True,

                "goal_difference_gap_verified":
                    True,

                "recent_points_gap_verified":
                    True,

                "recent_goal_difference_gap_verified":
                    True,

                "venue_form_points_gap_verified":
                    True,

                "five_signal_support_score_verified":
                    True,

                "context_alignment_verified":
                    True,

                "entropy_verified":
                    True,

                "normalized_entropy_verified":
                    True,

                "confidence_band_verified":
                    True,

                "uncertainty_band_verified":
                    True,

                "explanation_headline_verified":
                    True,

                "explanation_summary_verified":
                    True,

                "intelligence_artifacts_unchanged":
                    True,
            },

            "verification_counts": {

                "base_value_checks":
                    base_value_checks,

                "semantic_fixture_checks":
                    semantic_fixture_checks,

                "context_signals_per_fixture":
                    5,

                "derived_gap_fields_per_fixture":
                    6,
            },

            "rules": {

                "entropy":
                    "SHANNON_NATURAL_LOG",

                "normalized_entropy_denominator":
                    "LN_3",

                "support_score_min":
                    -5,

                "support_score_max":
                    5,

                "support_signal_count":
                    5,

                "alignment_values":
                    sorted(
                        ALLOWED_ALIGNMENTS
                    ),

                "confidence_band_values":
                    sorted(
                        ALLOWED_BANDS
                    ),

                "uncertainty_band_values":
                    sorted(
                        ALLOWED_BANDS
                    ),
            },

            "safety": {

                "read_only":
                    True,

                "model_loaded":
                    False,

                "model_executed":
                    False,

                "model_modified":
                    False,

                "probabilities_modified":
                    False,

                "prediction_labels_modified":
                    False,

                "context_modified":
                    False,

                "provider_fetch_performed":
                    False,

                "future_results_used":
                    False,

                "bookmaker_odds_used":
                    False,

                "intelligence_rebuilt":
                    False,
            },

            "dependency_identity": {

                relative_path(
                    FOUNDATION_FILE
                ): {
                    "sha256":
                        sha256_file(
                            FOUNDATION_FILE
                        ),
                },

                relative_path(
                    PREDICTION_INTEGRITY_FILE
                ): {
                    "sha256":
                        sha256_file(
                            PREDICTION_INTEGRITY_FILE
                        ),
                },

                relative_path(
                    CONTRACT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            CONTRACT_FILE
                        ),
                },

                relative_path(
                    BASE_FILE
                ): {
                    "sha256":
                        sha256_file(
                            BASE_FILE
                        ),
                },

                relative_path(
                    BASE_REPORT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            BASE_REPORT_FILE
                        ),
                },

                relative_path(
                    INTELLIGENCE_FILE
                ): {
                    "sha256":
                        sha256_file(
                            INTELLIGENCE_FILE
                        ),
                },

                relative_path(
                    INTELLIGENCE_REPORT_FILE
                ): {
                    "sha256":
                        sha256_file(
                            INTELLIGENCE_REPORT_FILE
                        ),
                },
            },

            "promotion": {

                "stage_9_complete":
                    False,

                "stage_9_8_complete":
                    False,

                "promotion_authorized":
                    False,

                "promotion_owner":
                    "9.8.5",
            },

            "stage9_ready_for_9_8_4":
                True,

            "next_stage":
                "9.8.4",

            "failures":
                [],
        }

        save_json_atomic(
            OUTPUT_FILE,
            evidence,
        )

        print(
            OUTPUT_FILE
        )

    # ========================================================
    # Final output
    # ========================================================

    print(
        "\n" + "=" * 72
    )

    if overall_pass:

        print(
            "STAGE 9.8.3: PASS"
        )

        print(
            "INTELLIGENCE INTEGRITY VERIFICATION: VERIFIED"
        )

        print(
            "DERIVED MATCH INTELLIGENCE: "
            "INDEPENDENTLY RECOMPUTED"
        )

        print(
            "STAGE 9 READY FOR 9.8.4"
        )

        print()

        print(
            "STAGE 9 IS NOT YET PROMOTED"
        )

    else:

        print(
            "STAGE 9.8.3: FAIL"
        )

        print(
            "INTELLIGENCE INTEGRITY VERIFICATION: "
            "NOT VERIFIED"
        )

        if failures:

            print(
                "\nFailures:"
            )

            for failure in failures:

                print(
                    f"  - {failure}"
                )

    print("=" * 72)

    sys.exit(
        0
        if overall_pass
        else 1
    )


if __name__ == "__main__":

    main()