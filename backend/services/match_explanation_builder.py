"""
FixtureIQ Stage 9.5
Deterministic Match Explanation Engine.

Populates only:

- stage9_explanation_headline
- stage9_explanation_summary

Rules:
- deterministic templates only
- no LLM generation
- no model loading/execution
- no probability modification
- no prediction-label modification
- no source-confidence modification
- no context-score modification
- no confidence/uncertainty modification
- no bookmaker odds
- no outcome tuning
- no future results

Stage 9.5 explains the verified prediction.
It does not create a new prediction.
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

INTELLIGENCE_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence.csv"
)

REPORT_FILE = (
    INTELLIGENCE_DIR
    / "match_intelligence_report.json"
)


# ============================================================
# Stage 9.5 contract
# ============================================================

EXPLANATION_VERSION = (
    "STAGE9_5_DETERMINISTIC_EXPLANATION_V1"
)

EXPLANATION_FIELDS = [

    "stage9_explanation_headline",
    "stage9_explanation_summary",
]

ALLOWED_PREDICTION_LABELS = {

    "Home Win",
    "Draw",
    "Away Win",
}

ALLOWED_ALIGNMENTS = {

    "SUPPORTIVE",
    "MIXED",
    "CONTRADICTORY",
    "NEUTRAL",
}

ALLOWED_BANDS = {

    "VERY_LOW",
    "LOW",
    "MODERATE",
    "HIGH",
    "VERY_HIGH",
}

FORBIDDEN_RESULT_CLAIMS = [

    "guaranteed win",
    "certain win",
    "sure win",
    "safe bet",
    "will definitely win",
    "will win for sure",
    "guaranteed draw",
    "certain draw",
]


# ============================================================
# Exceptions
# ============================================================

class MatchExplanationBuildError(
    RuntimeError
):
    pass


# ============================================================
# File helpers
# ============================================================

def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise MatchExplanationBuildError(
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

        raise MatchExplanationBuildError(
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

        raise MatchExplanationBuildError(
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

        raise MatchExplanationBuildError(
            f"CSV has no columns: {path}"
        )

    if not rows:

        raise MatchExplanationBuildError(
            f"CSV has no rows: {path}"
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

    if not path.exists():

        raise MatchExplanationBuildError(
            f"Artifact missing: {path}"
        )

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


# ============================================================
# Protected-column snapshot
# ============================================================

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


# ============================================================
# Numeric helpers
# ============================================================

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

        raise MatchExplanationBuildError(
            f"Empty numeric field: {field}"
        )

    try:

        value = Decimal(
            raw
        )

    except InvalidOperation as exc:

        raise MatchExplanationBuildError(
            (
                f"Invalid numeric value "
                f"{field}={raw!r}"
            )
        ) from exc

    if not value.is_finite():

        raise MatchExplanationBuildError(
            f"Non-finite value: {field}"
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

        raise MatchExplanationBuildError(
            f"{field} must be integer-like."
        )

    return int(
        value
    )


def percent_text(
    probability: Decimal,
) -> str:

    percentage = (
        probability
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
    probability_margin: Decimal,
) -> str:

    value = (
        probability_margin
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
        f"{value}"
    )


def directional_vote(
    value: int,
) -> int:

    if value > 0:

        return 1

    if value < 0:

        return -1

    return 0


# ============================================================
# Context-signal reconstruction
# ============================================================

def context_signal_counts(
    row: dict[str, str],
) -> tuple[
    int,
    int,
    int,
    int,
]:

    league_gap = integer_value(
        row,
        "stage9_league_position_gap",
    )

    points_gap = integer_value(
        row,
        "stage9_points_gap",
    )

    goal_difference_gap = integer_value(
        row,
        "stage9_goal_difference_gap",
    )

    recent_points_gap = integer_value(
        row,
        "stage9_recent_points_gap",
    )

    venue_gap = integer_value(
        row,
        "stage9_venue_form_points_gap",
    )

    votes = [

        directional_vote(
            league_gap
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

    home_venue_available = integer_value(
        row,
        "home_team_home_form_matches_available",
    )

    away_venue_available = integer_value(
        row,
        "away_team_away_form_matches_available",
    )

    if (
        home_venue_available > 0
        and
        away_venue_available > 0
    ):

        votes.append(
            directional_vote(
                venue_gap
            )
        )

    else:

        votes.append(
            0
        )

    if len(
        votes
    ) != 5:

        raise MatchExplanationBuildError(
            "Expected five context signals."
        )

    support_score = sum(
        votes
    )

    recorded_score = integer_value(
        row,
        "stage9_context_support_score",
    )

    if (
        support_score
        != recorded_score
    ):

        raise MatchExplanationBuildError(
            (
                "Context support-score reconstruction "
                "does not match Stage 9.3."
            )
        )

    home_count = sum(
        1
        for vote in votes
        if vote == 1
    )

    away_count = sum(
        1
        for vote in votes
        if vote == -1
    )

    neutral_count = sum(
        1
        for vote in votes
        if vote == 0
    )

    return (
        home_count,
        away_count,
        neutral_count,
        support_score,
    )


# ============================================================
# Explanation templates
# ============================================================

def headline_for(
    *,
    predicted_label: str,
    alignment: str,
    home_team: str,
    away_team: str,
) -> str:

    if predicted_label == "Home Win":

        if alignment == "SUPPORTIVE":

            return (
                f"Model leans {home_team}; "
                "context supports the home side"
            )

        if alignment == "CONTRADICTORY":

            return (
                f"Model leans {home_team}; "
                f"context favors {away_team}"
            )

        if alignment == "MIXED":

            return (
                f"Model leans {home_team}; "
                "context is mixed"
            )

        return (
            f"Model leans {home_team}; "
            "context is balanced"
        )

    if predicted_label == "Away Win":

        if alignment == "SUPPORTIVE":

            return (
                f"Model leans {away_team}; "
                "context supports the away side"
            )

        if alignment == "CONTRADICTORY":

            return (
                f"Model leans {away_team}; "
                f"context favors {home_team}"
            )

        if alignment == "MIXED":

            return (
                f"Model leans {away_team}; "
                "context is mixed"
            )

        return (
            f"Model leans {away_team}; "
            "context is balanced"
        )

    if predicted_label == "Draw":

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

    raise MatchExplanationBuildError(
        (
            "Unsupported predicted label: "
            f"{predicted_label!r}"
        )
    )


def summary_for(
    row: dict[str, str],
) -> str:

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

    predicted_label = str(
        row.get(
            "stage7_predicted_label",
            "",
        )
    ).strip()

    alignment = str(
        row.get(
            "stage9_context_alignment",
            "",
        )
    ).strip()

    confidence_band = str(
        row.get(
            "stage9_confidence_band",
            "",
        )
    ).strip()

    uncertainty_band = str(
        row.get(
            "stage9_uncertainty_band",
            "",
        )
    ).strip()

    if not home_team or not away_team:

        raise MatchExplanationBuildError(
            "Team name missing."
        )

    if (
        predicted_label
        not in ALLOWED_PREDICTION_LABELS
    ):

        raise MatchExplanationBuildError(
            "Invalid prediction label."
        )

    if (
        alignment
        not in ALLOWED_ALIGNMENTS
    ):

        raise MatchExplanationBuildError(
            "Invalid context alignment."
        )

    if (
        confidence_band
        not in ALLOWED_BANDS
    ):

        raise MatchExplanationBuildError(
            "Invalid confidence band."
        )

    if (
        uncertainty_band
        not in ALLOWED_BANDS
    ):

        raise MatchExplanationBuildError(
            "Invalid uncertainty band."
        )

    top_probability = decimal_value(
        row,
        "stage9_top_probability",
    )

    probability_margin = decimal_value(
        row,
        "stage9_probability_margin",
    )

    (
        home_signals,
        away_signals,
        neutral_signals,
        support_score,
    ) = context_signal_counts(
        row
    )

    if predicted_label == "Home Win":

        prediction_subject = home_team

    elif predicted_label == "Away Win":

        prediction_subject = away_team

    else:

        prediction_subject = "a draw"

    return (
        f"Stage 7 gives {prediction_subject} the highest "
        f"probability at {percent_text(top_probability)}, "
        f"{percentage_point_text(probability_margin)} "
        "percentage points above the next outcome. "
        f"The fixed context score is {support_score:+d}: "
        f"{home_signals} signals favor {home_team}, "
        f"{away_signals} favor {away_team}, and "
        f"{neutral_signals} are neutral or unavailable. "
        f"Context alignment is {alignment.lower()}; "
        f"confidence is {confidence_band.lower()} and "
        f"uncertainty is {uncertainty_band.lower()}. "
        "This interprets the existing prediction and "
        "does not alter or replace it."
    )


def validate_explanation_language(
    headline: str,
    summary: str,
) -> None:

    combined = (
        f"{headline} {summary}"
    ).lower()

    for forbidden in (
        FORBIDDEN_RESULT_CLAIMS
    ):

        if forbidden in combined:

            raise MatchExplanationBuildError(
                (
                    "Forbidden certainty language "
                    f"detected: {forbidden!r}"
                )
            )


# ============================================================
# Builder
# ============================================================

class MatchExplanationBuilder:

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

    def build(
        self,
    ) -> dict:

        # ====================================================
        # Stage 9.1
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

            raise MatchExplanationBuildError(
                "Stage 9.1 contract is not locked."
            )

        if (
            contract.get(
                "stage_9_1_complete"
            )
            is not True
        ):

            raise MatchExplanationBuildError(
                "Stage 9.1 is incomplete."
            )

        if (
            verification.get(
                "status"
            )
            != "PASS"
        ):

            raise MatchExplanationBuildError(
                "Stage 9.1 verification not PASS."
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

            raise MatchExplanationBuildError(
                "Stage 9.1 contract SHA mismatch."
            )

        # ====================================================
        # Stage 9.2
        # ====================================================

        base_report = load_json(
            self.base_report_file
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

            raise MatchExplanationBuildError(
                "Stage 9.2 is not complete."
            )

        if (
            base_report.get(
                "base_artifact",
                {}
            ).get(
                "sha256"
            )
            !=
            sha256_file(
                self.base_file
            )
        ):

            raise MatchExplanationBuildError(
                "Stage 9.2 base artifact stale."
            )

        # ====================================================
        # Stage 9.4
        # ====================================================

        report = load_json(
            self.report_file
        )

        if (
            report.get(
                "stage_9_3_complete"
            )
            is not True
        ):

            raise MatchExplanationBuildError(
                "Stage 9.3 evidence missing."
            )

        if (
            report.get(
                "stage_9_4_complete"
            )
            is not True
        ):

            raise MatchExplanationBuildError(
                "Stage 9.4 is incomplete."
            )

        if (
            report.get(
                "confidence_uncertainty_layer"
            )
            != "VERIFIED"
        ):

            raise MatchExplanationBuildError(
                (
                    "Confidence & uncertainty layer "
                    "is not VERIFIED."
                )
            )

        if (
            report.get(
                "stage9_ready_for_9_5"
            )
            is not True
        ):

            raise MatchExplanationBuildError(
                "Stage 9.4 did not authorize Stage 9.5."
            )

        stage9_4_sha = sha256_file(
            self.intelligence_file
        )

        if (
            report.get(
                "output_artifact",
                {}
            ).get(
                "sha256"
            )
            != stage9_4_sha
        ):

            raise MatchExplanationBuildError(
                "Stage 9.4 artifact is stale."
            )

        # ====================================================
        # Schema
        # ====================================================

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

        (
            fields,
            rows,
        ) = load_csv(
            self.intelligence_file
        )

        if (
            fields
            != final_fields
        ):

            raise MatchExplanationBuildError(
                "Final intelligence schema mismatch."
            )

        for field in EXPLANATION_FIELDS:

            if field not in fields:

                raise MatchExplanationBuildError(
                    (
                        "Missing explanation field: "
                        f"{field}"
                    )
                )

        # Explanations must still be blank before 9.5.
        for row in rows:

            for field in EXPLANATION_FIELDS:

                if (
                    row.get(
                        field,
                        ""
                    )
                    != ""
                ):

                    raise MatchExplanationBuildError(
                        (
                            "Explanation field already populated: "
                            f"{row.get('fixture_id')}, {field}"
                        )
                    )

        # ====================================================
        # Capture immutable Stage 9.4 snapshot
        # ====================================================

        protected_sha = (
            protected_snapshot_sha256(
                fields,
                rows,
            )
        )

        # ====================================================
        # Generate explanations
        # ====================================================

        output_rows = []

        seen_fixture_ids = set()

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

            fixture_id = str(
                row.get(
                    "fixture_id",
                    "",
                )
            ).strip()

            if not fixture_id:

                raise MatchExplanationBuildError(
                    "Empty fixture_id."
                )

            if fixture_id in seen_fixture_ids:

                raise MatchExplanationBuildError(
                    (
                        "Duplicate fixture_id: "
                        f"{fixture_id}"
                    )
                )

            seen_fixture_ids.add(
                fixture_id
            )

            predicted_label = str(
                row.get(
                    "stage7_predicted_label",
                    "",
                )
            ).strip()

            alignment = str(
                row.get(
                    "stage9_context_alignment",
                    "",
                )
            ).strip()

            if (
                predicted_label
                not in ALLOWED_PREDICTION_LABELS
            ):

                raise MatchExplanationBuildError(
                    (
                        "Unexpected prediction label: "
                        f"{predicted_label}"
                    )
                )

            if (
                alignment
                not in ALLOWED_ALIGNMENTS
            ):

                raise MatchExplanationBuildError(
                    (
                        "Unexpected context alignment: "
                        f"{alignment}"
                    )
                )

            # Confirm context score still reconstructs.
            context_signal_counts(
                row
            )

            headline = headline_for(

                predicted_label=
                    predicted_label,

                alignment=
                    alignment,

                home_team=
                    row[
                        "home_team_name"
                    ],

                away_team=
                    row[
                        "away_team_name"
                    ],
            )

            summary = summary_for(
                row
            )

            validate_explanation_language(
                headline,
                summary,
            )

            if not headline.strip():

                raise MatchExplanationBuildError(
                    "Generated empty headline."
                )

            if not summary.strip():

                raise MatchExplanationBuildError(
                    "Generated empty summary."
                )

            output_row = dict(
                row
            )

            output_row[
                "stage9_explanation_headline"
            ] = headline

            output_row[
                "stage9_explanation_summary"
            ] = summary

            output_rows.append(
                output_row
            )

            prediction_counts[
                predicted_label
            ] += 1

            alignment_counts[
                alignment
            ] += 1

        # ====================================================
        # Make sure only explanation fields changed
        # ====================================================

        output_protected_sha = (
            protected_snapshot_sha256(
                fields,
                output_rows,
            )
        )

        if (
            output_protected_sha
            != protected_sha
        ):

            raise MatchExplanationBuildError(
                (
                    "A pre-Stage-9.5 field changed "
                    "during explanation generation."
                )
            )

        return {

            "status":
                "PASS",

            "fields":
                fields,

            "rows":
                output_rows,

            "fixture_count":
                len(
                    output_rows
                ),

            "stage9_4_input_sha256":
                stage9_4_sha,

            "protected_snapshot_sha256":
                protected_sha,

            "output_protected_snapshot_sha256":
                output_protected_sha,

            "prediction_counts":
                prediction_counts,

            "alignment_counts":
                alignment_counts,

            "explanation_version":
                EXPLANATION_VERSION,

            "deterministic_templates":
                True,

            "llm_generation_used":
                False,

            "model_loaded":
                False,

            "model_executed":
                False,

            "probabilities_modified":
                False,

            "prediction_labels_modified":
                False,

            "source_confidence_modified":
                False,

            "context_intelligence_modified":
                False,

            "confidence_uncertainty_modified":
                False,

            "bookmaker_odds_used":
                False,

            "outcome_tuning_used":
                False,

            "future_results_used":
                False,
        }

    def build_and_write(
        self,
    ) -> dict:

        result = self.build()

        write_csv_atomic(
            self.intelligence_file,
            result[
                "fields"
            ],
            result[
                "rows"
            ],
        )

        result[
            "output_sha256"
        ] = sha256_file(
            self.intelligence_file
        )

        return result