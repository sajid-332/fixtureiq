"""
FixtureIQ Stage 9.5
Independent Match Explanation Validator.

Does not reuse MatchExplanationBuilder.
"""

from __future__ import annotations

import csv
import hashlib
import json
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)
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

INTELLIGENCE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)


EXPLANATION_FIELDS = [

    "stage9_explanation_headline",
    "stage9_explanation_summary",
]


class MatchExplanationValidationError(
    RuntimeError
):
    pass


def load_json(
    path: Path,
) -> dict:

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

        raise MatchExplanationValidationError(
            f"Expected JSON object: {path}"
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

        return (
            list(
                reader.fieldnames
                or []
            ),
            [
                dict(row)
                for row in reader
            ],
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


def protected_snapshot_sha256(
    fields: list[str],
    rows: list[dict[str, str]],
) -> str:

    protected_fields = [

        field

        for field in fields

        if field not in EXPLANATION_FIELDS
    ]

    payload = {

        "fields":
            protected_fields,

        "rows": [

            [
                row.get(
                    field,
                    ""
                )

                for field in protected_fields
            ]

            for row in rows
        ],
    }

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        serialized
    ).hexdigest()


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

        raise MatchExplanationValidationError(
            f"Invalid decimal {field}."
        ) from exc

    if not value.is_finite():

        raise MatchExplanationValidationError(
            f"Non-finite value {field}."
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

        raise MatchExplanationValidationError(
            f"{field} is not integer-like."
        )

    return int(
        value
    )


def percent_text(
    value: Decimal,
) -> str:

    percentage = (
        value
        *
        Decimal(
            "100"
        )
    ).quantize(
        Decimal(
            "0.1"
        ),
        rounding=ROUND_HALF_UP,
    )

    return (
        f"{percentage}%"
    )


def percentage_point_text(
    value: Decimal,
) -> str:

    percentage = (
        value
        *
        Decimal(
            "100"
        )
    ).quantize(
        Decimal(
            "0.1"
        ),
        rounding=ROUND_HALF_UP,
    )

    return str(
        percentage
    )


def vote(
    value: int,
) -> int:

    if value > 0:

        return 1

    if value < 0:

        return -1

    return 0


def signal_counts(
    row: dict[str, str],
) -> tuple[
    int,
    int,
    int,
    int,
]:

    votes = [

        vote(
            integer_value(
                row,
                "stage9_league_position_gap",
            )
        ),

        vote(
            integer_value(
                row,
                "stage9_points_gap",
            )
        ),

        vote(
            integer_value(
                row,
                "stage9_goal_difference_gap",
            )
        ),

        vote(
            integer_value(
                row,
                "stage9_recent_points_gap",
            )
        ),
    ]

    home_available = integer_value(
        row,
        "home_team_home_form_matches_available",
    )

    away_available = integer_value(
        row,
        "away_team_away_form_matches_available",
    )

    if (
        home_available > 0
        and
        away_available > 0
    ):

        votes.append(
            vote(
                integer_value(
                    row,
                    "stage9_venue_form_points_gap",
                )
            )
        )

    else:

        votes.append(
            0
        )

    score = sum(
        votes
    )

    if (
        score
        !=
        integer_value(
            row,
            "stage9_context_support_score",
        )
    ):

        raise MatchExplanationValidationError(
            "Context support-score mismatch."
        )

    return (

        sum(
            1
            for value in votes
            if value == 1
        ),

        sum(
            1
            for value in votes
            if value == -1
        ),

        sum(
            1
            for value in votes
            if value == 0
        ),

        score,
    )


def expected_headline(
    row: dict[str, str],
) -> str:

    label = row[
        "stage7_predicted_label"
    ]

    alignment = row[
        "stage9_context_alignment"
    ]

    home = row[
        "home_team_name"
    ]

    away = row[
        "away_team_name"
    ]

    if label == "Home Win":

        if alignment == "SUPPORTIVE":

            return (
                f"Model leans {home}; "
                "context supports the home side"
            )

        if alignment == "CONTRADICTORY":

            return (
                f"Model leans {home}; "
                f"context favors {away}"
            )

        if alignment == "MIXED":

            return (
                f"Model leans {home}; "
                "context is mixed"
            )

        return (
            f"Model leans {home}; "
            "context is balanced"
        )

    if label == "Away Win":

        if alignment == "SUPPORTIVE":

            return (
                f"Model leans {away}; "
                "context supports the away side"
            )

        if alignment == "CONTRADICTORY":

            return (
                f"Model leans {away}; "
                f"context favors {home}"
            )

        if alignment == "MIXED":

            return (
                f"Model leans {away}; "
                "context is mixed"
            )

        return (
            f"Model leans {away}; "
            "context is balanced"
        )

    if label == "Draw":

        if alignment == "SUPPORTIVE":

            return (
                "Model leans draw; "
                "context is relatively balanced"
            )

        if alignment == "MIXED":

            return (
                "Model leans draw; "
                "context shows a mild side advantage"
            )

        if alignment == "CONTRADICTORY":

            return (
                "Model leans draw; "
                "context shows a clearer side advantage"
            )

        return (
            "Model leans draw; "
            "context is neutral"
        )

    raise MatchExplanationValidationError(
        "Unexpected prediction label."
    )


def expected_summary(
    row: dict[str, str],
) -> str:

    home = row[
        "home_team_name"
    ]

    away = row[
        "away_team_name"
    ]

    label = row[
        "stage7_predicted_label"
    ]

    alignment = row[
        "stage9_context_alignment"
    ]

    confidence = row[
        "stage9_confidence_band"
    ]

    uncertainty = row[
        "stage9_uncertainty_band"
    ]

    top_probability = decimal_value(
        row,
        "stage9_top_probability",
    )

    margin = decimal_value(
        row,
        "stage9_probability_margin",
    )

    (
        home_signals,
        away_signals,
        neutral_signals,
        score,
    ) = signal_counts(
        row
    )

    if label == "Home Win":

        subject = home

    elif label == "Away Win":

        subject = away

    elif label == "Draw":

        subject = "a draw"

    else:

        raise MatchExplanationValidationError(
            "Unexpected prediction label."
        )

    return (
        f"Stage 7 gives {subject} the highest "
        f"probability at {percent_text(top_probability)}, "
        f"{percentage_point_text(margin)} "
        "percentage points above the next outcome. "
        f"The fixed context score is {score:+d}: "
        f"{home_signals} signals favor {home}, "
        f"{away_signals} favor {away}, and "
        f"{neutral_signals} are neutral or unavailable. "
        f"Context alignment is {alignment.lower()}; "
        f"confidence is {confidence.lower()} and "
        f"uncertainty is {uncertainty.lower()}. "
        "This interprets the existing prediction and "
        "does not alter or replace it."
    )


class MatchExplanationValidator:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        base_file: Path = BASE_FILE,
        base_report_file: Path = BASE_REPORT_FILE,
        intelligence_file: Path = INTELLIGENCE_FILE,
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

        self.intelligence_file = Path(
            intelligence_file
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

        verification = load_json(
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

            raise MatchExplanationValidationError(
                "Stage 9.1 contract not locked."
            )

        if (
            verification.get(
                "contract_sha256"
            )
            !=
            sha256_file(
                self.contract_file
            )
        ):

            raise MatchExplanationValidationError(
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

            raise MatchExplanationValidationError(
                "Stage 9.2 not complete."
            )

        if (
            report.get(
                "stage_9_4_complete"
            )
            is not True
            or
            report.get(
                "confidence_uncertainty_layer"
            )
            != "VERIFIED"
        ):

            raise MatchExplanationValidationError(
                "Stage 9.4 not verified."
            )

        if (
            report.get(
                "stage_9_5_complete"
            )
            is not True
        ):

            raise MatchExplanationValidationError(
                "Stage 9.5 build evidence missing."
            )

        (
            fields,
            rows,
        ) = load_csv(
            self.intelligence_file
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

        final_fields = (
            schema.get(
                "final_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        if fields != final_fields:

            raise MatchExplanationValidationError(
                "Final schema mismatch."
            )

        if not rows:

            raise MatchExplanationValidationError(
                "No intelligence rows."
            )

        if len(
            {
                row[
                    "fixture_id"
                ]
                for row in rows
            }
        ) != len(
            rows
        ):

            raise MatchExplanationValidationError(
                "Duplicate fixture IDs."
            )

        # ====================================================
        # Protected Stage 9.4 snapshot
        # ====================================================

        expected_protected_sha = (
            report.get(
                "stage_9_4_snapshot",
                {}
            ).get(
                "protected_columns_sha256"
            )
        )

        actual_protected_sha = (
            protected_snapshot_sha256(
                fields,
                rows,
            )
        )

        if (
            expected_protected_sha
            != actual_protected_sha
        ):

            raise MatchExplanationValidationError(
                (
                    "Pre-Stage-9.5 fields changed "
                    "after Stage 9.4."
                )
            )

        # ====================================================
        # Explanations
        # ====================================================

        explanation_comparisons = 0

        alignment_counts = {

            "SUPPORTIVE": 0,
            "MIXED": 0,
            "CONTRADICTORY": 0,
            "NEUTRAL": 0,
        }

        prediction_counts = {

            "Home Win": 0,
            "Draw": 0,
            "Away Win": 0,
        }

        for row in rows:

            expected_h = expected_headline(
                row
            )

            expected_s = expected_summary(
                row
            )

            actual_h = row.get(
                "stage9_explanation_headline",
                "",
            )

            actual_s = row.get(
                "stage9_explanation_summary",
                "",
            )

            if actual_h != expected_h:

                raise MatchExplanationValidationError(
                    (
                        "Headline mismatch for fixture "
                        f"{row['fixture_id']}."
                    )
                )

            explanation_comparisons += 1

            if actual_s != expected_s:

                raise MatchExplanationValidationError(
                    (
                        "Summary mismatch for fixture "
                        f"{row['fixture_id']}."
                    )
                )

            explanation_comparisons += 1

            if not actual_h.strip():

                raise MatchExplanationValidationError(
                    "Empty headline."
                )

            if not actual_s.strip():

                raise MatchExplanationValidationError(
                    "Empty summary."
                )

            lowered = (
                f"{actual_h} {actual_s}"
            ).lower()

            forbidden = [

                "guaranteed win",
                "certain win",
                "sure win",
                "safe bet",
                "will definitely win",
                "will win for sure",
                "guaranteed draw",
                "certain draw",
            ]

            for phrase in forbidden:

                if phrase in lowered:

                    raise MatchExplanationValidationError(
                        (
                            "Forbidden certainty phrase: "
                            f"{phrase}"
                        )
                    )

            alignment_counts[
                row[
                    "stage9_context_alignment"
                ]
            ] += 1

            prediction_counts[
                row[
                    "stage7_predicted_label"
                ]
            ] += 1

        # ====================================================
        # Report
        # ====================================================

        if (
            report.get(
                "stage_9_5_rule_version"
            )
            !=
            "STAGE9_5_DETERMINISTIC_EXPLANATION_V1"
        ):

            raise MatchExplanationValidationError(
                "Explanation rule version mismatch."
            )

        if (
            report.get(
                "output_artifact",
                {}
            ).get(
                "sha256"
            )
            !=
            sha256_file(
                self.intelligence_file
            )
        ):

            raise MatchExplanationValidationError(
                "Output SHA mismatch."
            )

        statistics = report.get(
            "stage_9_5_statistics",
            {}
        )

        if (
            statistics.get(
                "prediction_counts"
            )
            != prediction_counts
        ):

            raise MatchExplanationValidationError(
                "Prediction counts mismatch."
            )

        if (
            statistics.get(
                "alignment_counts"
            )
            != alignment_counts
        ):

            raise MatchExplanationValidationError(
                "Alignment counts mismatch."
            )

        explanation_contract = report.get(
            "explanation_contract",
            {}
        )

        if (
            explanation_contract.get(
                "engine"
            )
            !=
            "DETERMINISTIC_TEMPLATE_ENGINE"
        ):

            raise MatchExplanationValidationError(
                "Explanation engine contract mismatch."
            )

        if (
            explanation_contract.get(
                "llm_generation"
            )
            is not False
        ):

            raise MatchExplanationValidationError(
                "LLM generation contract invalid."
            )

        return {

            "status":
                "PASS",

            "fixture_count":
                len(
                    rows
                ),

            "schema_exact":
                True,

            "fixture_ids_unique":
                True,

            "protected_stage9_4_snapshot_exact":
                True,

            "headlines_exact":
                True,

            "summaries_exact":
                True,

            "deterministic_templates_exact":
                True,

            "context_score_reconstruction_exact":
                True,

            "non_guaranteed_language_verified":
                True,

            "explanation_comparisons":
                explanation_comparisons,

            "prediction_counts":
                prediction_counts,

            "alignment_counts":
                alignment_counts,

            "output_sha256":
                sha256_file(
                    self.intelligence_file
                ),
        }