"""
FixtureIQ Stage 9.3
Derived Match Intelligence Builder.

Input:
    match_intelligence_base.csv

Output:
    match_intelligence.csv

Stage 9.3 derives deterministic descriptive intelligence only.

It does NOT:
- load or execute the ML model
- change Stage 7 probabilities
- change Stage 7 prediction labels
- change Stage 7 confidence
- use final-test data
- use bookmaker odds
- use future results
- perform outcome-based tuning

Stage 9.4-owned fields remain blank:
- entropy
- normalized entropy
- confidence band
- uncertainty band

Stage 9.5-owned explanation fields remain blank.
"""

from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


# ============================================================
# Paths
# ============================================================

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


# ============================================================
# Stage ownership
# ============================================================

STAGE9_3_POPULATED_FIELDS = {

    "stage9_top_probability",
    "stage9_second_probability",
    "stage9_probability_margin",

    "stage9_league_position_gap",
    "stage9_points_gap",
    "stage9_goal_difference_gap",

    "stage9_recent_points_gap",
    "stage9_recent_goal_difference_gap",

    "stage9_venue_form_points_gap",

    "stage9_context_support_score",
    "stage9_context_alignment",
}


STAGE9_4_RESERVED_FIELDS = {

    "stage9_entropy",
    "stage9_normalized_entropy",
    "stage9_confidence_band",
    "stage9_uncertainty_band",
}


STAGE9_5_RESERVED_FIELDS = {

    "stage9_explanation_headline",
    "stage9_explanation_summary",
}


# ============================================================
# Exceptions
# ============================================================

class MatchIntelligenceBuildError(
    RuntimeError
):
    pass


# ============================================================
# Helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise MatchIntelligenceBuildError(
            f"Required JSON missing: {path}"
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

        raise MatchIntelligenceBuildError(
            f"Expected JSON object: {path}"
        )

    return payload


def load_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:

    if not path.exists():

        raise MatchIntelligenceBuildError(
            f"Required CSV missing: {path}"
        )

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

    if not fields:

        raise MatchIntelligenceBuildError(
            f"No CSV columns: {path}"
        )

    if not rows:

        raise MatchIntelligenceBuildError(
            f"No CSV rows: {path}"
        )

    return (
        fields,
        rows,
    )


def write_csv_atomic(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="raise",
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    temporary.replace(
        path
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


def relative_path(
    path: Path,
) -> str:

    return (
        str(
            path.relative_to(
                BASE_DIR
            )
        )
        .replace(
            "\\",
            "/",
        )
    )


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

    if not raw:

        raise MatchIntelligenceBuildError(
            f"Empty numeric field {field!r}."
        )

    try:

        value = Decimal(
            raw
        )

    except InvalidOperation as exc:

        raise MatchIntelligenceBuildError(
            (
                f"Invalid decimal value for "
                f"{field!r}: {raw!r}"
            )
        ) from exc

    if not value.is_finite():

        raise MatchIntelligenceBuildError(
            f"Non-finite value in {field!r}."
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

    integral = value.to_integral_value()

    if value != integral:

        raise MatchIntelligenceBuildError(
            (
                f"Expected integer-like value "
                f"for {field!r}: {value}"
            )
        )

    return int(
        integral
    )


def decimal_text(
    value: Decimal,
) -> str:

    return format(
        value,
        "f",
    )


def directional_vote(
    gap: int,
) -> int:

    if gap > 0:

        return 1

    if gap < 0:

        return -1

    return 0


def context_alignment(
    predicted_label: str,
    support_score: int,
) -> str:

    # -----------------------------------------------
    # Home prediction
    # -----------------------------------------------

    if predicted_label == "Home Win":

        if support_score >= 2:

            return "SUPPORTIVE"

        if support_score <= -2:

            return "CONTRADICTORY"

        if support_score == 0:

            return "NEUTRAL"

        return "MIXED"

    # -----------------------------------------------
    # Away prediction
    # -----------------------------------------------

    if predicted_label == "Away Win":

        if support_score <= -2:

            return "SUPPORTIVE"

        if support_score >= 2:

            return "CONTRADICTORY"

        if support_score == 0:

            return "NEUTRAL"

        return "MIXED"

    # -----------------------------------------------
    # Draw prediction
    # -----------------------------------------------

    if predicted_label == "Draw":

        absolute_score = abs(
            support_score
        )

        if absolute_score <= 1:

            return "SUPPORTIVE"

        if absolute_score == 2:

            return "MIXED"

        return "CONTRADICTORY"

    raise MatchIntelligenceBuildError(
        (
            "Unsupported Stage 7 prediction label: "
            f"{predicted_label!r}"
        )
    )


# ============================================================
# Builder
# ============================================================

class MatchIntelligenceBuilder:

    def __init__(
        self,
        *,
        contract_file: Path = CONTRACT_FILE,
        contract_verification_file: Path = CONTRACT_VERIFICATION_FILE,
        base_file: Path = BASE_FILE,
        base_report_file: Path = BASE_REPORT_FILE,
        output_file: Path = OUTPUT_FILE,
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

    def build(
        self,
    ) -> dict:

        # ====================================================
        # Contract
        # ====================================================

        contract = load_json(
            self.contract_file
        )

        verification = load_json(
            self.contract_verification_file
        )

        if (
            contract.get(
                "status"
            )
            !=
            "LOCKED_MATCH_INTELLIGENCE_CONTRACT"
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.1 contract is not locked."
            )

        if (
            contract.get(
                "stage_9_1_complete"
            )
            is not True
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.1 is incomplete."
            )

        if (
            verification.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.1 verification is not PASS."
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

            raise MatchIntelligenceBuildError(
                "Stage 9.1 contract SHA mismatch."
            )

        # ====================================================
        # Stage 9.2 final gate
        # ====================================================

        base_report = load_json(
            self.base_report_file
        )

        if (
            base_report.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.2 report is not PASS."
            )

        if (
            base_report.get(
                "stage_9_2_complete"
            )
            is not True
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.2 is incomplete."
            )

        if (
            base_report.get(
                "prediction_context_join_layer"
            )
            != "VERIFIED"
        ):

            raise MatchIntelligenceBuildError(
                (
                    "Prediction-context join layer "
                    "is not VERIFIED."
                )
            )

        if (
            base_report.get(
                "final_gate",
                {}
            ).get(
                "stage9_ready_for_9_3"
            )
            is not True
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.2 did not authorize Stage 9.3."
            )

        base_artifact = base_report.get(
            "base_artifact",
            {}
        )

        if (
            base_artifact.get(
                "sha256"
            )
            !=
            sha256_file(
                self.base_file
            )
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.2 base artifact is stale."
            )

        # ====================================================
        # Locked schema
        # ====================================================

        canonical_schema = (
            contract.get(
                "stage_9_1_3",
                {}
            ).get(
                "canonical_schema",
                {}
            )
        )

        locked_base_fields = (
            canonical_schema.get(
                "base_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        derived_fields = (
            canonical_schema.get(
                "derived_intelligence_fields",
                {}
            ).get(
                "fields",
                [],
            )
        )

        locked_final_fields = (
            canonical_schema.get(
                "final_intelligence_schema",
                {}
            ).get(
                "fields",
                [],
            )
        )

        expected_derived = (
            STAGE9_3_POPULATED_FIELDS
            |
            STAGE9_4_RESERVED_FIELDS
            |
            STAGE9_5_RESERVED_FIELDS
        )

        if (
            set(
                derived_fields
            )
            != expected_derived
        ):

            raise MatchIntelligenceBuildError(
                (
                    "Locked derived schema differs "
                    "from Stage 9 ownership contract."
                )
            )

        expected_final_fields = (
            list(
                locked_base_fields
            )
            +
            list(
                derived_fields
            )
        )

        if (
            expected_final_fields
            != locked_final_fields
        ):

            raise MatchIntelligenceBuildError(
                "Locked final schema is inconsistent."
            )

        # ====================================================
        # Base artifact
        # ====================================================

        (
            base_fields,
            base_rows,
        ) = load_csv(
            self.base_file
        )

        if (
            base_fields
            != locked_base_fields
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.2 base schema changed."
            )

        if (
            len(
                base_rows
            )
            !=
            base_artifact.get(
                "fixture_count"
            )
        ):

            raise MatchIntelligenceBuildError(
                "Stage 9.2 fixture count changed."
            )

        # ====================================================
        # Derive Stage 9.3
        # ====================================================

        output_rows = []

        seen_fixture_ids = set()

        for base_row in base_rows:

            fixture_id = str(
                base_row.get(
                    "fixture_id",
                    "",
                )
            ).strip()

            if not fixture_id:

                raise MatchIntelligenceBuildError(
                    "Empty fixture_id in Stage 9.2 base."
                )

            if fixture_id in seen_fixture_ids:

                raise MatchIntelligenceBuildError(
                    (
                        "Duplicate fixture_id in "
                        f"Stage 9.2 base: {fixture_id}"
                    )
                )

            seen_fixture_ids.add(
                fixture_id
            )

            # -----------------------------------------------
            # Stage 7 probabilities
            # -----------------------------------------------

            probability_items = [

                (
                    "Home Win",
                    decimal_value(
                        base_row,
                        "stage7_prob_home_win",
                    ),
                ),

                (
                    "Draw",
                    decimal_value(
                        base_row,
                        "stage7_prob_draw",
                    ),
                ),

                (
                    "Away Win",
                    decimal_value(
                        base_row,
                        "stage7_prob_away_win",
                    ),
                ),
            ]

            sorted_probabilities = sorted(

                probability_items,

                key=lambda item:
                    item[1],

                reverse=True,
            )

            top_probability = (
                sorted_probabilities[
                    0
                ][
                    1
                ]
            )

            second_probability = (
                sorted_probabilities[
                    1
                ][
                    1
                ]
            )

            probability_margin = (
                top_probability
                -
                second_probability
            )

            predicted_label = str(
                base_row.get(
                    "stage7_predicted_label",
                    "",
                )
            ).strip()

            if (
                predicted_label
                !=
                sorted_probabilities[
                    0
                ][
                    0
                ]
            ):

                raise MatchIntelligenceBuildError(
                    (
                        f"Stage 7 prediction label does not "
                        f"match probability argmax for "
                        f"fixture {fixture_id}."
                    )
                )

            # -----------------------------------------------
            # Context gaps
            #
            # Positive values favor home.
            # Negative values favor away.
            # -----------------------------------------------

            league_position_gap = (

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

            goal_difference_gap = (

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

            recent_goal_difference_gap = (

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

            venue_form_points_gap = (

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

            # -----------------------------------------------
            # Fixed five-component support score
            # -----------------------------------------------

            support_votes = [

                directional_vote(
                    league_position_gap
                ),

                directional_vote(
                    points_gap
                ),

                directional_vote(
                    goal_difference_gap
                ),

                directional_vote(
                    recent_points_gap
                ),
            ]

            home_venue_available = (
                integer_value(
                    base_row,
                    "home_team_home_form_matches_available",
                )
            )

            away_venue_available = (
                integer_value(
                    base_row,
                    "away_team_away_form_matches_available",
                )
            )

            if (
                home_venue_available > 0
                and
                away_venue_available > 0
            ):

                support_votes.append(
                    directional_vote(
                        venue_form_points_gap
                    )
                )

            else:

                # Missing venue sample is neutral,
                # never treated as poor form.
                support_votes.append(
                    0
                )

            if (
                len(
                    support_votes
                )
                != 5
            ):

                raise MatchIntelligenceBuildError(
                    "Context support component count != 5."
                )

            support_score = sum(
                support_votes
            )

            if not (
                -5
                <= support_score
                <= 5
            ):

                raise MatchIntelligenceBuildError(
                    "Context support score outside [-5,5]."
                )

            alignment = context_alignment(
                predicted_label,
                support_score,
            )

            # -----------------------------------------------
            # Build exact locked final schema
            # -----------------------------------------------

            derived_values = {

                "stage9_top_probability":
                    decimal_text(
                        top_probability
                    ),

                "stage9_second_probability":
                    decimal_text(
                        second_probability
                    ),

                "stage9_probability_margin":
                    decimal_text(
                        probability_margin
                    ),

                # Stage 9.4 owns these.
                "stage9_entropy":
                    "",

                "stage9_normalized_entropy":
                    "",

                "stage9_confidence_band":
                    "",

                "stage9_uncertainty_band":
                    "",

                "stage9_league_position_gap":
                    str(
                        league_position_gap
                    ),

                "stage9_points_gap":
                    str(
                        points_gap
                    ),

                "stage9_goal_difference_gap":
                    str(
                        goal_difference_gap
                    ),

                "stage9_recent_points_gap":
                    str(
                        recent_points_gap
                    ),

                "stage9_recent_goal_difference_gap":
                    str(
                        recent_goal_difference_gap
                    ),

                "stage9_venue_form_points_gap":
                    str(
                        venue_form_points_gap
                    ),

                "stage9_context_support_score":
                    str(
                        support_score
                    ),

                "stage9_context_alignment":
                    alignment,

                # Stage 9.5 owns these.
                "stage9_explanation_headline":
                    "",

                "stage9_explanation_summary":
                    "",
            }

            output_row = {

                field:
                    base_row.get(
                        field,
                        "",
                    )

                for field in locked_base_fields
            }

            for field in derived_fields:

                output_row[
                    field
                ] = derived_values[
                    field
                ]

            if (
                list(
                    output_row.keys()
                )
                != locked_final_fields
            ):

                raise MatchIntelligenceBuildError(
                    "Final output field order changed."
                )

            output_rows.append(
                output_row
            )

        return {

            "status":
                "PASS",

            "fields":
                locked_final_fields,

            "rows":
                output_rows,

            "fixture_count":
                len(
                    output_rows
                ),

            "column_count":
                len(
                    locked_final_fields
                ),

            "base_column_count":
                len(
                    locked_base_fields
                ),

            "derived_column_count":
                len(
                    derived_fields
                ),

            "stage9_3_populated_field_count":
                len(
                    STAGE9_3_POPULATED_FIELDS
                ),

            "stage9_4_reserved_field_count":
                len(
                    STAGE9_4_RESERVED_FIELDS
                ),

            "stage9_5_reserved_field_count":
                len(
                    STAGE9_5_RESERVED_FIELDS
                ),

            "base_values_preserved_exactly":
                True,

            "probabilities_modified":
                False,

            "prediction_labels_modified":
                False,

            "source_confidence_modified":
                False,

            "context_support_component_count":
                5,

            "context_support_score_min":
                -5,

            "context_support_score_max":
                5,

            "rule_version":
                "STAGE9_3_DERIVED_INTELLIGENCE_V1",

            "contract_sha256":
                sha256_file(
                    self.contract_file
                ),

            "contract_verification_sha256":
                sha256_file(
                    self.contract_verification_file
                ),

            "base_sha256":
                sha256_file(
                    self.base_file
                ),

            "base_report_sha256":
                sha256_file(
                    self.base_report_file
                ),
        }

    def build_and_write(
        self,
    ) -> dict:

        result = self.build()

        write_csv_atomic(
            self.output_file,
            result[
                "fields"
            ],
            result[
                "rows"
            ],
        )

        result[
            "output_path"
        ] = relative_path(
            self.output_file
        )

        result[
            "output_sha256"
        ] = sha256_file(
            self.output_file
        )

        return result