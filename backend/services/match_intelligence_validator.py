"""
FixtureIQ Stage 9.3
Independent Derived Match Intelligence Validator.

Does not reuse MatchIntelligenceBuilder.
"""

from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
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

CONTRACT_VERIFICATION_FILE = (
    INTELLIGENCE_DIR
    / "stage9_intelligence_contract_verification.json"
)

BASE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base.csv"
)

BASE_REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_base_report.json"
)

OUTPUT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)


class MatchIntelligenceValidationError(
    RuntimeError
):
    pass


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise MatchIntelligenceValidationError(
            f"Missing JSON: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(
            file
        )

    if not isinstance(
        payload,
        dict,
    ):

        raise MatchIntelligenceValidationError(
            f"Expected object: {path}"
        )

    return payload


def load_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        fields = list(
            reader.fieldnames
            or []
        )

        rows = [
            dict(row)
            for row in reader
        ]

    return (
        fields,
        rows,
    )


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:

                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def decimal_value(
    row: dict[str, str],
    field: str,
) -> Decimal:

    raw = str(
        row.get(
            field,
            "",
        )
    ).strip()

    try:

        value = Decimal(
            raw
        )

    except InvalidOperation as exc:

        raise MatchIntelligenceValidationError(
            (
                f"Invalid decimal {field}: "
                f"{raw!r}"
            )
        ) from exc

    if not value.is_finite():

        raise MatchIntelligenceValidationError(
            f"Non-finite {field}."
        )

    return value


def integer_value(
    row: dict[str, str],
    field: str,
) -> int:

    value = decimal_value(
        row,
        field,
    )

    if (
        value
        !=
        value.to_integral_value()
    ):

        raise MatchIntelligenceValidationError(
            f"{field} is not integer-like."
        )

    return int(
        value
    )


def text_decimal(
    value: Decimal,
) -> str:

    return format(
        value,
        "f",
    )


def vote(
    value: int,
) -> int:

    if value > 0:

        return 1

    if value < 0:

        return -1

    return 0


def alignment(
    label: str,
    score: int,
) -> str:

    if label == "Home Win":

        if score >= 2:
            return "SUPPORTIVE"

        if score <= -2:
            return "CONTRADICTORY"

        if score == 0:
            return "NEUTRAL"

        return "MIXED"

    if label == "Away Win":

        if score <= -2:
            return "SUPPORTIVE"

        if score >= 2:
            return "CONTRADICTORY"

        if score == 0:
            return "NEUTRAL"

        return "MIXED"

    if label == "Draw":

        if abs(score) <= 1:
            return "SUPPORTIVE"

        if abs(score) == 2:
            return "MIXED"

        return "CONTRADICTORY"

    raise MatchIntelligenceValidationError(
        f"Unexpected prediction label {label!r}."
    )


class MatchIntelligenceValidator:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        base_file: Path = BASE_FILE,
        base_report_file: Path = BASE_REPORT_FILE,
        output_file: Path = OUTPUT_FILE,
        report_file: Path = REPORT_FILE,
    ) -> None:

        self.contract_file = Path(
            contract_file
        )

        self.contract_verification_file = Path(
            contract_verification_file
        )

        self.base_file = Path(
            base_file
        )

        self.base_report_file = Path(
            base_report_file
        )

        self.output_file = Path(
            output_file
        )

        self.report_file = Path(
            report_file
        )

    def validate(
        self,
    ) -> dict:

        contract = load_json(
            self.contract_file
        )

        contract_verification = load_json(
            self.contract_verification_file
        )

        base_report = load_json(
            self.base_report_file
        )

        report = load_json(
            self.report_file
        )

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise MatchIntelligenceValidationError(
                "Stage 9.1 contract not locked."
            )

        if (
            contract_verification.get(
                "contract_sha256"
            )
            !=
            sha256_file(
                self.contract_file
            )
        ):

            raise MatchIntelligenceValidationError(
                "Contract SHA mismatch."
            )

        if (
            base_report.get(
                "status"
            )
            != "PASS"
            or
            base_report.get(
                "stage_9_2_complete"
            )
            is not True
        ):

            raise MatchIntelligenceValidationError(
                "Stage 9.2 not complete."
            )

        if (
            report.get(
                "status"
            )
            != "PASS"
            or
            report.get(
                "stage_9_3_complete"
            )
            is not True
        ):

            raise MatchIntelligenceValidationError(
                "Stage 9.3 report not PASS."
            )

        (
            base_fields,
            base_rows,
        ) = load_csv(
            self.base_file
        )

        (
            output_fields,
            output_rows,
        ) = load_csv(
            self.output_file
        )

        schema = (
            contract.get(
                "stage_9_1_3",
                {}
            ).get(
                "canonical_schema",
                {}
            )
        )

        locked_base_fields = (
            schema.get(
                "base_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        final_fields = (
            schema.get(
                "final_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        if (
            base_fields
            != locked_base_fields
        ):

            raise MatchIntelligenceValidationError(
                "Base schema mismatch."
            )

        if (
            output_fields
            != final_fields
        ):

            raise MatchIntelligenceValidationError(
                "Final schema mismatch."
            )

        if (
            len(
                base_rows
            )
            !=
            len(
                output_rows
            )
        ):

            raise MatchIntelligenceValidationError(
                "Row count mismatch."
            )

        base_index = {}
        output_index = {}

        base_order = []
        output_order = []

        for row in base_rows:

            fixture_id = row[
                "fixture_id"
            ]

            if fixture_id in base_index:

                raise MatchIntelligenceValidationError(
                    "Duplicate base fixture."
                )

            base_index[
                fixture_id
            ] = row

            base_order.append(
                fixture_id
            )

        for row in output_rows:

            fixture_id = row[
                "fixture_id"
            ]

            if fixture_id in output_index:

                raise MatchIntelligenceValidationError(
                    "Duplicate output fixture."
                )

            output_index[
                fixture_id
            ] = row

            output_order.append(
                fixture_id
            )

        if (
            set(
                base_index
            )
            !=
            set(
                output_index
            )
        ):

            raise MatchIntelligenceValidationError(
                "Fixture sets differ."
            )

        if (
            base_order
            != output_order
        ):

            raise MatchIntelligenceValidationError(
                "Fixture order changed."
            )

        base_comparisons = 0
        derived_comparisons = 0

        for fixture_id in base_order:

            base_row = base_index[
                fixture_id
            ]

            output_row = output_index[
                fixture_id
            ]

            # -----------------------------------------------
            # Exact Stage 9.2 preservation
            # -----------------------------------------------

            for field in base_fields:

                if (
                    output_row.get(
                        field
                    )
                    !=
                    base_row.get(
                        field
                    )
                ):

                    raise MatchIntelligenceValidationError(
                        (
                            f"Base value changed: "
                            f"{fixture_id}, {field}"
                        )
                    )

                base_comparisons += 1

            probabilities = sorted(

                [

                    decimal_value(
                        base_row,
                        "stage7_prob_home_win",
                    ),

                    decimal_value(
                        base_row,
                        "stage7_prob_draw",
                    ),

                    decimal_value(
                        base_row,
                        "stage7_prob_away_win",
                    ),
                ],

                reverse=True,
            )

            top = probabilities[
                0
            ]

            second = probabilities[
                1
            ]

            margin = (
                top
                -
                second
            )

            league_gap = (

                integer_value(
                    base_row,
                    "away_team_position",
                )
                -
                integer_value(
                    base_row,
                    "home_team_position",
                )
            )

            points_gap = (

                integer_value(
                    base_row,
                    "home_team_points",
                )
                -
                integer_value(
                    base_row,
                    "away_team_points",
                )
            )

            gd_gap = (

                integer_value(
                    base_row,
                    "home_team_goal_difference",
                )
                -
                integer_value(
                    base_row,
                    "away_team_goal_difference",
                )
            )

            recent_points_gap = (

                integer_value(
                    base_row,
                    "home_team_recent_points",
                )
                -
                integer_value(
                    base_row,
                    "away_team_recent_points",
                )
            )

            recent_gd_gap = (

                integer_value(
                    base_row,
                    "home_team_recent_goal_difference",
                )
                -
                integer_value(
                    base_row,
                    "away_team_recent_goal_difference",
                )
            )

            venue_gap = (

                integer_value(
                    base_row,
                    "home_team_home_recent_points",
                )
                -
                integer_value(
                    base_row,
                    "away_team_away_recent_points",
                )
            )

            score_parts = [

                vote(
                    league_gap
                ),

                vote(
                    points_gap
                ),

                vote(
                    gd_gap
                ),

                vote(
                    recent_points_gap
                ),
            ]

            home_available = integer_value(
                base_row,
                "home_team_home_form_matches_available",
            )

            away_available = integer_value(
                base_row,
                "away_team_away_form_matches_available",
            )

            if (
                home_available > 0
                and
                away_available > 0
            ):

                score_parts.append(
                    vote(
                        venue_gap
                    )
                )

            else:

                score_parts.append(
                    0
                )

            score = sum(
                score_parts
            )

            expected = {

                "stage9_top_probability":
                    text_decimal(
                        top
                    ),

                "stage9_second_probability":
                    text_decimal(
                        second
                    ),

                "stage9_probability_margin":
                    text_decimal(
                        margin
                    ),

                "stage9_league_position_gap":
                    str(
                        league_gap
                    ),

                "stage9_points_gap":
                    str(
                        points_gap
                    ),

                "stage9_goal_difference_gap":
                    str(
                        gd_gap
                    ),

                "stage9_recent_points_gap":
                    str(
                        recent_points_gap
                    ),

                "stage9_recent_goal_difference_gap":
                    str(
                        recent_gd_gap
                    ),

                "stage9_venue_form_points_gap":
                    str(
                        venue_gap
                    ),

                "stage9_context_support_score":
                    str(
                        score
                    ),

                "stage9_context_alignment":
                    alignment(
                        base_row[
                            "stage7_predicted_label"
                        ],
                        score,
                    ),
            }

            for field, expected_value in (
                expected.items()
            ):

                if (
                    output_row.get(
                        field
                    )
                    != expected_value
                ):

                    raise MatchIntelligenceValidationError(
                        (
                            f"Derived mismatch: "
                            f"{fixture_id}, {field}; "
                            f"expected {expected_value!r}, "
                            f"got "
                            f"{output_row.get(field)!r}"
                        )
                    )

                derived_comparisons += 1

            # -----------------------------------------------
            # Stage 9.4 must still be untouched
            # -----------------------------------------------

            for field in (

                "stage9_entropy",
                "stage9_normalized_entropy",
                "stage9_confidence_band",
                "stage9_uncertainty_band",
            ):

                if (
                    output_row.get(
                        field,
                        ""
                    )
                    != ""
                ):

                    raise MatchIntelligenceValidationError(
                        (
                            f"Stage 9.4 field populated "
                            f"early: {field}"
                        )
                    )

            # -----------------------------------------------
            # Stage 9.5 must still be untouched
            # -----------------------------------------------

            for field in (

                "stage9_explanation_headline",
                "stage9_explanation_summary",
            ):

                if (
                    output_row.get(
                        field,
                        ""
                    )
                    != ""
                ):

                    raise MatchIntelligenceValidationError(
                        (
                            f"Stage 9.5 field populated "
                            f"early: {field}"
                        )
                    )

        artifact = report.get(
            "output_artifact",
            {}
        )

        if (
            artifact.get(
                "sha256"
            )
            !=
            sha256_file(
                self.output_file
            )
        ):

            raise MatchIntelligenceValidationError(
                "Stage 9.3 output SHA mismatch."
            )

        dependencies = report.get(
            "dependency_identity",
            {}
        )

        expected_dependencies = {

            "stage9_intelligence_contract":
                self.contract_file,

            "stage9_intelligence_contract_verification":
                self.contract_verification_file,

            "match_intelligence_base":
                self.base_file,

            "match_intelligence_base_report":
                self.base_report_file,
        }

        for name, path in (
            expected_dependencies.items()
        ):

            if (
                dependencies.get(
                    name,
                    {}
                ).get(
                    "sha256"
                )
                !=
                sha256_file(
                    path
                )
            ):

                raise MatchIntelligenceValidationError(
                    f"Stale dependency: {name}"
                )

        return {

            "status":
                "PASS",

            "fixture_count":
                len(
                    output_rows
                ),

            "column_count":
                len(
                    output_fields
                ),

            "fixture_sets_exact":
                True,

            "fixture_order_preserved":
                True,

            "base_schema_exact":
                True,

            "final_schema_exact":
                True,

            "base_values_exact":
                True,

            "probability_metrics_exact":
                True,

            "context_gaps_exact":
                True,

            "context_support_score_exact":
                True,

            "context_alignment_exact":
                True,

            "stage9_4_fields_blank":
                True,

            "stage9_5_fields_blank":
                True,

            "dependency_identity_current":
                True,

            "base_value_comparisons":
                base_comparisons,

            "derived_value_comparisons":
                derived_comparisons,

            "output_sha256":
                sha256_file(
                    self.output_file
                ),
        }